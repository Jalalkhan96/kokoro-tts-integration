#!/usr/bin/env bash
set -e
# Kokoro TTS - Linux/Mac Install (Python 3.10+)
python3 --version || { echo "Python 3.10+ install karo pehle"; exit 1; }
pip3 --version || python3 -m pip --version
command -v ffmpeg >/dev/null || echo "WARNING: sudo apt install -y ffmpeg espeak-ng"
command -v espeak-ng >/dev/null || echo "WARNING: sudo apt install -y espeak-ng"
python3 -m venv .venv
. .venv/bin/activate
pip install --upgrade pip
pip install torch --index-url https://download.pytorch.org/whl/cpu || pip install torch
pip install -r service/requirements.txt
pip install python-telegram-bot requests
echo "DONE. Test: python examples/test_local.py"
echo "Service: uvicorn app:app --port 8880  (service/ folder se)"
