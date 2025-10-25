## n8n Transcription Stack

This stack runs an n8n instance alongside a Python worker container that ships with `ffmpeg`, OpenAI Whisper, and CUDA-enabled PyTorch. It provides an out-of-the-box environment for building n8n workflows that rely on speech-to-text transcription and can leverage GPU acceleration when available.

### Prerequisites
- Docker 20.10+
- Docker Compose plugin v2+
- NVIDIA GPU with recent drivers
- NVIDIA Container Toolkit configured on the host (required so Docker exposes GPUs to the container)

### Usage
1. Build and start the services (GPU devices are requested automatically):
   ```bash
   docker compose up -d --build
   ```
2. Open n8n at http://localhost:5678 and create your workflows. The `whisper-worker` container is available on the internal Compose network (service name `whisper-worker`) for running custom Python scripts that use Whisper/PyTorch.
3. (Optional) Verify GPU access inside the worker:
   ```bash
   docker compose exec whisper-worker python3 -c "import torch; print(torch.cuda.is_available())"
   ```
   A value of `False` means the worker falls back to CPU execution, which still works (albeit slower).

### Containers
- `n8n`: Official `n8nio/n8n` image with persistent data volume at `n8n_data`.
- `whisper-worker`: Python 3.11 image with `ffmpeg`, `openai-whisper`, `torch`, and `torchaudio` preinstalled. A cache volume (`whisper_cache`) is mounted to persist Whisper model downloads.

### Customization
- Adjust environment variables for n8n inside `docker-compose.yml` as required.
- Add your own Python scripts or automation code under `whisper-worker/` and rebuild the image.

### API Endpoints
The worker exposes a FastAPI server on port `8000`:
- `POST /transcribe`: accepts a multipart form upload containing an audio/video file (`file` field). Optional query parameters allow changing the Whisper model (`model_name`) and target language (`language`).
- `POST /transcribe-url`: accepts JSON in the shape `{"url": "...", "language": "pt", "model": "base"}` and uses `yt-dlp` to download and transcribe the audio track.

Example request uploading a local file:
```bash
curl -X POST "http://localhost:8000/transcribe?language=en&model_name=small" \
  -F "file=@/path/to/audio.mp3"
```

Example request pointing at a YouTube URL:
```bash
curl -X POST "http://localhost:8000/transcribe-url" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://www.youtube.com/watch?v=dQw4w9WgXcQ","language":"en","model":"base"}'
```
The API responds with the transcription and the path to the persisted `.txt` file inside the shared `/data` volume.

### Sample Workflow
- Import `workflows/youtube-transcription.json` into n8n to download and transcribe video `kHp-vBJKnBU` (or edit the Set node to point at another video).
- The workflow sends a JSON request to `http://whisper-worker:8000/transcribe-url`; the worker downloads the audio with `yt-dlp`, transcribes it with Whisper, and returns the text.


---
![n8n wrkfl](n8n.png)