# Kokoro TTS API — tumhare bots ke liye

Base URL (deploy ke baad jo milega): `https://<tumhari-api>` — neeche `KOKORO_API` isi ko kehte hain.
Har request par header (agar API_KEY set hai): `x-api-key: <tumhari key>`

## Endpoints
```
GET  /health            -> {"ok": true, "model": "hexgrad/Kokoro-82M", "default_voice": "af_heart"}
GET  /voices            -> {"voices": ["af_heart","af_bella", ...]}
POST /tts               -> audio file (binary)
     Body: {"text":"Hello Jalal","voice":"af_heart","speed":1.0,"format":"ogg"}
     format: "ogg" = WhatsApp PTT + Telegram voice ke liye | "wav" | "mp3"
```

## curl test
```bash
curl -X POST $KOKORO_API/tts -H "Content-Type: application/json" -H "x-api-key: $KOKORO_API_KEY" \
  -d '{"text":"Hello, this is Kokoro speaking","voice":"af_heart","format":"ogg"}' --output test.ogg
```

## WhatsApp bot (Baileys) me sirf 2 env
```
KOKORO_API=https://<tumhari-api>
KOKORO_API_KEY=<tumhari key>
```
Phir `whatsapp_plugin/kokoro-tts.cjs` plugins folder me — commands: `-tts`, `-ttsaudio`, `-voices`

## Telegram bot me sirf 2 env
```
KOKORO_API=https://<tumhari-api>
KOKORO_API_KEY=<tumhari key>
```
`telegram_bot/bot.py` ready hai, ya apne existing Telegram bot se upar wala POST call kar lo.

## Node.js se direct call (kisi bhi bot me)
```js
const axios = require('axios');
const res = await axios.post(`${process.env.KOKORO_API}/tts`,
  { text: 'Hello', voice: 'af_heart', format: 'ogg' },
  { responseType: 'arraybuffer', headers: { 'x-api-key': process.env.KOKORO_API_KEY } });
await sock.sendMessage(jid, { audio: Buffer.from(res.data), mimetype: 'audio/ogg; codecs=opus', ptt: true });
```

## Hamesha-on (always-on) kahan chalegi?
| Jagah | Haal |
|---|---|
| Ye Muse sandbox | ❌ Public inbound traffic hi nahi ata — yahan se public API mumkin nahi |
| KataBump free (308MB RAM) | ❌ Model 325MB + runtime ~600MB, fit nahi hoga |
| Render Standard ($25/mo, 2GB) | ✅ Chalega — Free aur Starter dono 512MB hain, service ki peak RAM 558MB hai (measured) |
| Render Free + Starter (512MB) | ❌ Service peak RAM 558MB (measured 2026-10-22) — OOM kill hogi; Free 15 min me sota bhi hai |
| HuggingFace Spaces (free CPU, 16GB) | ✅ Free always-on option — Docker SDK se yehi Dockerfile chalega, lekin public space par API key lazmi rakho |
| Tumhari apni PC/VPS | ✅ `deploy/docker-compose.yml` — `restart: always`, PC band to API band (PC wale case me bots bhi aksar wahi hote hain) |
