import os
import subprocess
from typing import Optional

import torch
import whisper
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from yt_dlp import YoutubeDL
import shlex



# Diretório de trabalho
DATA_DIR = "./"
DATA_DIR = "/data"
os.makedirs(DATA_DIR, exist_ok=True)


# 🔹 Estrutura de resposta
class TranscriptionResponse(BaseModel):
    id: Optional[str] = None
    url: Optional[str] = None
    title: Optional[str] = None
    channel: Optional[str] = None
    publishedText: Optional[str] = None
    estimatedPublishedAt: Optional[str] = None
    text: str
    output_file: Optional[str] = None


# 🔹 Estrutura de entrada
class YoutubePayload(BaseModel):
    id: Optional[str] = None
    url: str
    title: Optional[str] = None
    channel: Optional[str] = None
    publishedText: Optional[str] = None
    estimatedPublishedAt: Optional[str] = None
    language: Optional[str] = "pt"
    model: Optional[str] = "base"


# 🔹 Inicialização do app e cache de modelos
app = FastAPI()
device = "cuda" if torch.cuda.is_available() else "cpu"
model_cache = {}


def get_model(name: str):
    if name not in model_cache:
        print(f"🔹 Carregando modelo Whisper: {name} ({device})")
        model_cache[name] = whisper.load_model(name).to(device)
    return model_cache[name]


@app.post("/transcribe-url", response_model=TranscriptionResponse)
async def transcribe_url(payload: YoutubePayload):
    """Baixa o áudio do YouTube e realiza a transcrição com fallback completo."""
    print("-------------------------------------------")
    print(payload.json)

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": os.path.join(DATA_DIR, "%(id)s.%(ext)s"),
        "quiet": False,
        "noplaylist": True,
        "geo_bypass": True,
        "retries": 5,
        "fragment_retries": 10,
        "http_chunk_size": 10 * 1024 * 1024,
        "concurrent_fragment_downloads": 1,
        "skip_unavailable_fragments": True,
        "default_search": "auto",
        "extractor_args": {
            "youtube": {"player_client": ["android", "web", "ios"]},  # ✅ força clients válidos
        },
        "http_headers": {
            "User-Agent": (
                "Mozilla/5.0 (Linux; Android 11; SM-G991B) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0 Mobile Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9,pt-BR;q=0.8",
        },
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "m4a",
                "preferredquality": "192",
            }
        ],
    }



    # 🔽 Download
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(payload.url, download=True)
            print(f"payload: {payload} | url: {payload.url} | info: {info}");
            download_path = info.get("filepath") or ydl.prepare_filename(info)

            # Caminho base correto
            base = os.path.splitext(ydl.prepare_filename(info))[0]

            # Busca o arquivo final gerado pelo postprocessor
            audio_exts = [".m4a", ".mp3", ".wav", ".ogg"]
            download_path = None
            for ext in audio_exts:
                candidate = base + ext
                if os.path.exists(candidate):
                    download_path = candidate
                    break

            # Se nada encontrado, tenta o nome original do info dict
            if not download_path and "requested_downloads" in info:
                for req in info["requested_downloads"]:
                    if os.path.exists(req.get("filepath", "")):
                        download_path = req["filepath"]
                        break

            if not download_path:
                raise HTTPException(status_code=400, detail="Nenhum arquivo de áudio encontrado.")


    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Download failed: {e}")

    print(f"✅ Download concluído: {download_path}")

    # 🔍 Verifica se o ffprobe reconhece áudio
    probe_cmd = [
        "ffprobe", "-v", "error", "-select_streams", "a:0",
        "-show_entries", "stream=codec_name",
        "-of", "default=nokey=1:noprint_wrappers=1",
        download_path
    ]
    probe = subprocess.run(probe_cmd, capture_output=True, text=True)

    # ⚙️ Fallback forçado se não detectar áudio
    if not probe.stdout.strip():
        print("⚠️ Nenhuma faixa de áudio detectada — aplicando extração forçada (raw demux nível 2)...")
        base = os.path.splitext(download_path)[0]
        fixed_path = base + "_fixed.wav"

        # 1️⃣ Tenta forçar o FFmpeg a tratar como fluxo genérico
        convert_cmd = shlex.split(
            f"ffmpeg -y -probesize 5000000 -analyzeduration 5000000 "
            f"-err_detect ignore_err -f data -i {shlex.quote(download_path)} "
            f"-vn -acodec pcm_s16le -ar 16000 -ac 1 {shlex.quote(fixed_path)}"
        )
        try:
            subprocess.run(convert_cmd, check=True)
            download_path = fixed_path
            print(f"✅ Conversão bruta concluída (modo data): {download_path}")
        except subprocess.CalledProcessError:
            print("⚠️ Tentativa 1 falhou — tentando modo sem tipo declarado...")
            convert_cmd2 = shlex.split(
                f"ffmpeg -y -err_detect ignore_err -i {shlex.quote(download_path)} "
                f"-vn -acodec pcm_s16le -ar 16000 -ac 1 {shlex.quote(fixed_path)}"
            )
            subprocess.run(convert_cmd2, check=True)
            download_path = fixed_path
            print(f"✅ Conversão bruta (modo livre) concluída: {download_path}")
    else:
        print(f"🎧 Áudio detectado ({probe.stdout.strip()}) — seguindo para transcrição.")

    # 🧠 Transcrição
    model = get_model(payload.model)
    try:
        print("🧠 Transcrevendo áudio...")
        result = model.transcribe(download_path, language=payload.language)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")
    finally:
        if os.path.exists(download_path):
            os.remove(download_path)

    # 💾 Salva transcrição
    output_path = f"{download_path}.txt"
    with open(output_path, "w", encoding="utf-8") as out:
        out.write(result["text"])

    print(f"📝 Transcrição salva em: {output_path}")

    return {**payload.dict(), "text": result["text"], "output_file": output_path}


# 🔹 Teste direto local
if __name__ == "__main__":
    import asyncio

    payload = YoutubePayload(
        id="1QiZPNnfY-I",
        url="https://www.youtube.com/watch?v=1QiZPNnfY-I",
        title="Russia may send nuclear weapons to Venezuela and Cuba.",
        channel="bellei",
        publishedText="1 hour ago",
        estimatedPublishedAt="2025-10-31T14:22:50.447Z",
        language="pt",
        model="base",
    )

    print("🚀 Testando transcrição direta (sem servidor)...")
    result = asyncio.run(transcribe_url(payload))
    print("\n✅ Resultado parcial:")
    print(result["text"][:400], "...")
