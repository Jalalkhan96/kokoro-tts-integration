# Kokoro TTS API — always-on Docker image (ONNX CPU, ~600MB RAM in use)
FROM python:3.10-slim
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg curl && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY service/requirements-onnx.txt .
RUN pip install --no-cache-dir -r requirements-onnx.txt
COPY service/tts_engine.py service/app.py ./
RUN mkdir -p models && \
    curl -L -o models/kokoro-v1.0.onnx https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx && \
    curl -L -o models/voices-v1.0.bin https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin
# tts_engine expects models/ next to it
ENV PORT=8880
EXPOSE 8880
CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port ${PORT}"]
