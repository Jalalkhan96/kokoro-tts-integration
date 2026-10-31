"""Direct local test — no bots, no server. Proves Kokoro runs on this CPU.
Run:  ../.venv/bin/python test_local.py   (from examples/ or adjust path)
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "service"))
from tts_engine import synthesize

wav = synthesize("Hello Jalal, this is Kokoro. Running fully offline on CPU, ready for Telegram and WhatsApp.", voice="af_heart")
out = os.path.join(os.path.dirname(__file__), "kokoro-test.wav")
open(out, "wb").write(wav)
print(f"OK -> {out}  ({len(wav)/1024:.0f} KB, 24kHz WAV)")
