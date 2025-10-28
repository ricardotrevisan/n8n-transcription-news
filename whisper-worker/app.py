import os
from typing import Optional

import torch
import whisper
from fastapi import FastAPI, HTTPException, UploadFile
from pydantic import BaseModel
from yt_dlp import YoutubeDL

DATA_DIR = "/data" 
os.makedirs(DATA_DIR, exist_ok=True)

class TranscriptionResponse(BaseModel):
    text: str
    output_file: Optional[str] = None


class YoutubePayload(BaseModel):
    url: str
    language: Optional[str] = "pt"
    model: Optional[str] = "base"


app = FastAPI()
device = "cuda" if torch.cuda.is_available() else "cpu"
model_cache = {}


def get_model(name: str):
    if name not in model_cache:
        model_cache[name] = whisper.load_model(name).to(device)
    return model_cache[name]

@app.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe(file: UploadFile, language: str = "pt", model_name: str = "base"):
    file_path = os.path.join(DATA_DIR, file.filename)
    with open(file_path, "wb") as f:
        f.write(await file.read())

    try:
        model = get_model(model_name)
        result = model.transcribe(file_path, language=language)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")
    finally:
        os.remove(file_path)

    output_path = file_path + ".txt"
    with open(output_path, "w", encoding="utf-8") as out:
        out.write(result["text"])

    return {"text": result["text"], "output_file": output_path}


@app.post("/transcribe-url", response_model=TranscriptionResponse)
async def transcribe_url(payload: YoutubePayload):
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": os.path.join(DATA_DIR, "%(id)s.%(ext)s"),
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "default_search": "auto",
        "cachedir": os.path.join(DATA_DIR, "yt-dlp"),
        "prefer_ffmpeg": True,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
        "keepvideo": False,
        # 🔧 Correções principais
        "http_headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/124.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9,pt-BR;q=0.8",
        },
        "geo_bypass": True,
        "retries": 5,
        "fragment_retries": 10,
        "skip_unavailable_fragments": True,
        "concurrent_fragment_downloads": 1,
        "http_chunk_size": 10 * 1024 * 1024,
        "extractor_args": {
            "youtube": {"player_client": ["android", "web"]}
        },
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(payload.url, download=True)
            download_path = info.get("filepath") or ydl.prepare_filename(info)

            for requested in info.get("requested_downloads", []):
                candidate = requested.get("filepath")
                if candidate and os.path.exists(candidate):
                    download_path = candidate
                    break

            if not os.path.exists(download_path):
                alt_path = download_path.rsplit(".", 1)[0] + ".mp3"
                if os.path.exists(alt_path):
                    download_path = alt_path
                else:
                    raise HTTPException(status_code=400, detail="Unable to download audio stream")
    except Exception as e:
        msg = str(e)
        if "403" in msg:
            raise HTTPException(status_code=403, detail="Acesso negado (HTTP 403). "
                                                        "Possível vídeo privado, bloqueio regional "
                                                        "ou headers desatualizados.")
        raise HTTPException(status_code=500, detail=f"Download failed: {msg}")

    print(f"Downloaded to {download_path}")
    model = get_model(payload.model)
    try:
        print('Transcribing...')
        result = model.transcribe(download_path, language=payload.language)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")
    finally:
        if os.path.exists(download_path):
            os.remove(download_path)

    output_path = download_path + ".txt"
    with open(output_path, "w", encoding="utf-8") as out:
        out.write(result["text"])

    return {"text": result["text"], "output_file": output_path}

