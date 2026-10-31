"""
Kokoro TTS Engine — shared core, dual backend
Official repo: https://github.com/hexgrad/kokoro
Model: hexgrad/Kokoro-82M (Apache 2.0, 82M params, CPU-friendly)

Backend A (preferred, his Windows PC): official `kokoro` pip package (PyTorch CPU)
Backend B (lightweight, verified in sandbox): `kokoro-onnx` (ONNX Runtime CPU)
  - needs service/models/kokoro-v1.0.onnx + voices-v1.0.bin
  - download: https://github.com/thewh1teagle/kokoro-onnx/releases/tag/model-files-v1.0
Both run 100% on Intel CPU — no GPU required.
Voices: af_heart (default), af_bella, af_sarah, am_adam, am_michael,
        bf_emma, bf_isabella, bm_george, bm_lewis, etc.
"""
import io, os, threading
import numpy as np
import soundfile as sf

_lock = threading.Lock()
_pipelines = {}
_onnx = None

DEFAULT_VOICE = os.getenv("KOKORO_VOICE", "af_heart")
SAMPLE_RATE = 24000
_MODELS_DIR = os.path.join(os.path.dirname(__file__), "models")
ONNX_MODEL = os.getenv("KOKORO_ONNX_MODEL", os.path.join(_MODELS_DIR, "kokoro-v1.0.onnx"))
ONNX_VOICES = os.getenv("KOKORO_ONNX_VOICES", os.path.join(_MODELS_DIR, "voices-v1.0.bin"))

def _backend():
    try:
        import kokoro  # noqa
        return "torch"
    except ImportError:
        return "onnx"

def _get_pipeline(lang_code: str = "a"):
    if lang_code not in _pipelines:
        from kokoro import KPipeline
        _pipelines[lang_code] = KPipeline(lang_code=lang_code)
    return _pipelines[lang_code]

def _get_onnx():
    global _onnx
    if _onnx is None:
        from kokoro_onnx import Kokoro
        if not (os.path.exists(ONNX_MODEL) and os.path.exists(ONNX_VOICES)):
            raise FileNotFoundError(
                f"ONNX model files missing in {_MODELS_DIR} — download kokoro-v1.0.onnx + voices-v1.0.bin "
                "from https://github.com/thewh1teagle/kokoro-onnx/releases/tag/model-files-v1.0 "
                "ya official torch backend install karo (pip install kokoro)."
            )
        _onnx = Kokoro(ONNX_MODEL, ONNX_VOICES)
    return _onnx

def lang_from_voice(voice: str) -> str:
    return voice[0] if voice and len(voice) >= 2 else "a"

# espeak lang per voice family (ONNX backend phonemizer). Voice ka pehla
# letter = language family: a=US English, b=UK English, e=Spanish,
# f=French, h=Hindi, i=Italian, j=Japanese, p=Portuguese, z=Mandarin.
# PEHLE YE HARDCODED en-us/en-gb THA — Hindi voice bhi English phonemes
# se bolti thi, is liye "kuch aur hi" sunai deta tha. (fix 2026-10-23)
ONNX_LANG = {
    "a": "en-us", "b": "en-gb", "e": "es", "f": "fr", "h": "hi",
    "i": "it", "j": "ja", "p": "pt-br", "z": "cmn",
}

def onnx_lang_for(voice: str, lang: str = None) -> str:
    if lang:
        return lang
    return ONNX_LANG.get((voice or "a")[:1].lower(), "en-us")

def synthesize(text: str, voice: str = DEFAULT_VOICE, speed: float = 1.0,
               lang: str = None) -> bytes:
    """Return WAV bytes (24kHz mono). Thread-safe.

    lang: optional espeak lang override (e.g. "ur" for Urdu-script text
    spoken with a Hindi voice — Kokoro has no Urdu voice, but espeak 'ur'
    phonemes + hm_omega/hf_* voice is the closest correct route).
    """
    text = (text or "").strip()
    if not text:
        raise ValueError("text is empty")
    if len(text) > 2000:
        text = text[:2000]
    with _lock:
        if _backend() == "torch":
            code = lang_from_voice(voice)
            if lang and len(lang) == 1:
                code = lang
            elif lang == "ur":
                code = "h"  # torch pipelines are single-letter; Urdu -> Hindi
            pipeline = _get_pipeline(code)
            chunks = []
            for _, _, audio in pipeline(text, voice=voice, speed=speed, split_pattern=r"\n+"):
                if audio is not None:
                    chunks.append(audio if isinstance(audio, np.ndarray) else np.asarray(audio))
            if not chunks:
                raise RuntimeError("Kokoro produced no audio")
            full = np.concatenate(chunks) if len(chunks) > 1 else chunks[0]
        else:
            kokoro = _get_onnx()
            full, sr = kokoro.create(text, voice=voice, speed=speed,
                                     lang=onnx_lang_for(voice, lang))
            if full is None or len(full) == 0:
                raise RuntimeError("Kokoro ONNX produced no audio")
    buf = io.BytesIO()
    sf.write(buf, full, SAMPLE_RATE, format="WAV")
    return buf.getvalue()

VOICES = [
    "af_heart","af_bella","af_sarah","af_nicole","af_sky",
    "am_adam","am_michael","am_echo","am_puck",
    "bf_emma","bf_isabella","bm_george","bm_lewis",
]
