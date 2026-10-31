"""
Kokoro TTS HTTP Service — one service, both bots use it.

Run:
  uvicorn app:app --host 0.0.0.0 --port 8880
  # or: python app.py

Endpoints:
  GET  /health
  GET  /voices
  POST /tts   {text, voice?, speed?, format?: wav|ogg|mp3} -> audio file
       format ogg = OGG/Opus (required for WhatsApp PTT + Telegram voice)

Why a separate service? WhatsApp bot is Node/Baileys, Telegram bot can be
Python or Node — neither should embed PyTorch. Both just POST here.
"""
import os, subprocess, tempfile
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import Response
from pydantic import BaseModel
from tts_engine import synthesize, VOICES, DEFAULT_VOICE

app = FastAPI(title="Kokoro TTS Service")

API_KEY = os.getenv("API_KEY", "")  # set this when deployed publicly!

@app.middleware("http")
async def check_key(request: Request, call_next):
    # /health stays public so Render/host health-checks work
    if API_KEY and request.url.path != "/health":
        if request.headers.get("x-api-key") != API_KEY:
            return Response(content='{"detail":"invalid API key"}', status_code=401, media_type="application/json")
    return await call_next(request)

class TTSRequest(BaseModel):
    text: str
    voice: str = DEFAULT_VOICE
    speed: float = 1.0
    format: str = "ogg"  # wav | ogg | mp3

@app.get("/health")
def health():
    return {"ok": True, "model": "hexgrad/Kokoro-82M", "default_voice": DEFAULT_VOICE}

@app.get("/voices")
def voices():
    return {"voices": VOICES}

def wav_to(wav_bytes: bytes, fmt: str) -> tuple[bytes, str]:
    if fmt == "wav":
        return wav_bytes, "audio/wav"
    if fmt not in ("ogg", "mp3"):
        raise HTTPException(400, "format must be wav, ogg or mp3")
    with tempfile.TemporaryDirectory() as d:
        src, dst = f"{d}/in.wav", f"{d}/out.{fmt}"
        open(src, "wb").write(wav_bytes)
        if fmt == "ogg":
            cmd = ["ffmpeg", "-y", "-i", src, "-c:a", "libopus", "-b:a", "32k", "-ar", "48000", dst]
        else:
            cmd = ["ffmpeg", "-y", "-i", src, "-c:a", "libmp3lame", "-q:a", "4", dst]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            raise HTTPException(500, f"ffmpeg failed: {r.stderr[-500:]}")
        return open(dst, "rb").read(), ("audio/ogg" if fmt == "ogg" else "audio/mpeg")

@app.post("/tts")
def tts(req: TTSRequest):
    try:
        wav = synthesize(req.text, voice=req.voice, speed=min(max(req.speed, 0.5), 2.0))
    except Exception as e:
        raise HTTPException(500, str(e))
    data, media = wav_to(wav, req.format.lower())
    return Response(content=data, media_type=media)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8880")))
