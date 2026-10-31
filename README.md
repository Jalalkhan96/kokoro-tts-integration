# Kokoro TTS + Telegram & WhatsApp Integration

Official Kokoro: https://github.com/hexgrad/kokoro — Kokoro-82M, Apache 2.0, sirf 82M params.
**Intel CPU par bhi chalta hai** — GPU lazmi nahi. CPU version hi use karna hai.

**Short answer: YES — Telegram aur WhatsApp dono ke saath integrate ho sakta hai.**
Architecture ek hi hai: Kokoro ek chhoti si HTTP service (port 8880) ban jati hai,
Telegram bot aur WhatsApp (Baileys) bot dono usi service ko call karte hain.
Is se PyTorch ko Node.js ke andar ghusane ki zaroorat nahi padti.

```
Telegram user ──> telegram_bot/bot.py ──┐
                                         ├──> service/app.py (Kokoro) ──> WAV ──ffmpeg──> OGG/Opus
WhatsApp user ──> whatsapp_plugin/*.cjs ─┘                                              │
                              Telegram: reply_voice()        WhatsApp: sendMessage(ptt:true)
```

---

## Tumhare Steps — Windows par bilkul isi order mein

### Step 1: Python 3.10 (Recommended) install karo
- https://www.python.org/downloads/release/python-31011/ → Windows installer (64-bit)
- **Installer ki pehli screen par `Add python.exe to PATH` lazmi tick karna** — yehi Step 2 hai asal mein.

### Step 2: Environment Variable mein PATH add karna
Agar installer mein tick kar diya tha to ye already ho gaya. Warna manually:
`Settings → Search "environment variables" → Environment Variables → Path → Edit → New`:
```
C:\Users\<tumhara naam>\AppData\Local\Programs\Python\Python310\
C:\Users\<tumhara naam>\AppData\Local\Programs\Python\Python310\Scripts\
```

### Step 3: Check karo dono proper work kar rahi hain
**Naya** CMD kholo (purana CMD naya PATH nahi uthayega) aur paste karo:
```cmd
python --version
pip --version
```
Expected:
```
Python 3.10.11
pip 23.x from ...\Python310\lib\site-packages\pip (python 3.10)
```
Agar `python` likhne par Microsoft Store khul jaye → `Settings → App execution aliases → python.exe OFF` karo.

### Step 4: Baaki deps
- **espeak-ng** (Kokoro ki dependency): https://github.com/espeak-ng/espeak-ng/releases se MSI
- **ffmpeg** (voice-note conversion ke liye): https://www.gyan.dev/ffmpeg/builds/

### Step 5: Project install — ek command
```cmd
install-windows.bat
```
Ya manually:
```cmd
python -m venv .venv
.venv\Scripts\activate
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -r service\requirements.txt
```

### Step 6: Test (bots se pehle sirf Kokoro)
```cmd
python examples\test_local.py
:: -> examples\kokoro-test.wav banegi, play karke sun lo
```
Pehli dafa ~330MB model HuggingFace se download hoga, phir hamesha offline.

---

## Service chalao (dono bots ke liye lazmi)
```cmd
cd service
..\.venv\Scripts\uvicorn.exe app:app --host 0.0.0.0 --port 8880
```
Check: browser mein `http://127.0.0.1:8880/health` → `{"ok": true, ...}`
Direct test:
```cmd
curl -X POST http://127.0.0.1:8880/tts -H "Content-Type: application/json" -d "{\"text\":\"Hello, this is Kokoro\",\"voice\":\"af_heart\",\"format\":\"ogg\"}" --output test.ogg
```

## Telegram Integration
```cmd
set TELEGRAM_BOT_TOKEN=<@BotFather wala token>
set KOKORO_API=http://127.0.0.1:8880
pip install python-telegram-bot requests
python telegram_bot\bot.py
```
Chat mein: `/tts Hello` ya bas plain text bhejo → **voice note** ayega.
Voice change: `/tts af_bella | Hello` — `/voices` se list milti hai.
*Technical note:* Telegram `sendVoice` sirf OGG/Opus leta hai — service `format:"ogg"` mein ffmpeg se wahi bana kar deti hai, is liye direct WAV bhejna fail hota.

## WhatsApp Integration (Baileys, CommonJS)
1. `whatsapp_plugin/kokoro-tts.cjs` ko apne bot ke plugins folder mein copy karo (`require()` style, tumhari standing convention).
2. Bot ke main handler mein: `await handleKokoro(sock, msg)` — ya plugin loader khud `commands:['tts','ttsaudio','voices']` utha lega.
3. Chat commands (tumhara `-` prefix):
   - `-tts Salaam, main Kokoro bol rahi hoon` → **PTT voice note**
   - `-tts af_bella | Hello` → specific voice
   - `-ttsaudio <text>` → audio file (PTT nahi)
   - `-voices` → voice list
*Technical note:* WhatsApp PTT ke liye `ptt:true` + `audio/ogg; codecs=opus` lazmi hai — plugin mein dono set hain.

## Voices (kuch mashhoor)
`af_heart` (default, US female) · `af_bella` · `af_sarah` · `am_adam` · `am_michael` ·
`bf_emma` (British female) · `bf_isabella` · `bm_george` · `bm_lewis`
Note: Kokoro mein abhi Urdu voice nahi hai — Urdu text par English phonetics ayengi, quality weak hogi. English text best hai.

## Files
```
service/tts_engine.py      Kokoro core (KPipeline wrapper, thread-safe)
service/app.py             FastAPI service  GET /health /voices, POST /tts
service/requirements.txt
telegram_bot/bot.py        Telegram bot (python-telegram-bot)
whatsapp_plugin/kokoro-tts.cjs  Baileys plugin (.cjs)
examples/test_local.py     Sirf Kokoro ka test, koi bot nahi
install-windows.bat / install-linux.sh
```

---
## Verified in sandbox (2026-10-22)
- ONNX CPU generation: test sentence -> 300 KB / 24 kHz WAV, ~19 s incl. model load (after load ~2-4 s per sentence)
- GET /health OK - GET /voices 13 voices - POST /tts ogg -> valid Opus 48 kHz mono (4.06 s), exact WhatsApp PTT / Telegram voice format - wav OK - bad format -> 400
- WhatsApp plugin mock test 3/3 - Python + JS syntax OK - API-key middleware added (bots send x-api-key when KOKORO_API_KEY set)
- Hamesha-on API ke liye dekho: API.md + deploy/ (Dockerfile / render.yaml / docker-compose.yml)
- Model files ZIP me nahi hain (338 MB) - pehli dafa service/models/ me ye 2 files rakho: kokoro-v1.0.onnx + voices-v1.0.bin
  Download: https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/
  (Docker deploy me ye khud download ho jati hain.)
