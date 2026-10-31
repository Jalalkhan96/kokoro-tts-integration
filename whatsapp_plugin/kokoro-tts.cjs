/**
 * WhatsApp (Baileys) + Kokoro TTS plugin — CommonJS, drop-in for ABIX-style bots.
 * Prefix rule (standing): commands use `-`  e.g.  -tts Hello boss
 *
 * Setup:
 *   1. Run the Python service:  cd ../service && uvicorn app:app --port 8880
 *   2. Copy this file into your bot's plugins folder.
 *   3. Env: KOKORO_API=http://127.0.0.1:8880  (default)
 *
 * Usage in chat:
 *   -tts <text>                  -> voice note (PTT)
 *   -tts af_bella | <text>       -> specific voice
 *   -ttsaudio <text>             -> audio file (not PTT)
 *   -voices                      -> list voices
 *
 * How it plugs in: most Baileys bots expose a handler registry.
 * This file exports BOTH a generic handler and a ready register() —
 * adapt the one line marked ADAPT if your bot's loader differs.
 */
const axios = require('axios');

const API = process.env.KOKORO_API || 'http://127.0.0.1:8880';
const API_KEY = process.env.KOKORO_API_KEY || '';
const DEFAULT_VOICE = process.env.KOKORO_VOICE || 'af_heart';
const HEADERS = API_KEY ? { 'x-api-key': API_KEY } : {};

async function kokoroTTS(text, voice = DEFAULT_VOICE, format = 'ogg') {
  const res = await axios.post(
    `${API}/tts`,
    { text, voice, format },
    { responseType: 'arraybuffer', timeout: 120000, headers: HEADERS }
  );
  return Buffer.from(res.data);
}

async function handleKokoro(sock, msg) {
  const from = msg.key.remoteJid;
  const body =
    msg.message?.conversation ||
    msg.message?.extendedTextMessage?.text ||
    '';
  if (!body.startsWith('-')) return false;

  const [cmdRaw, ...rest] = body.slice(1).trim().split(/\s+/);
  const cmd = cmdRaw.toLowerCase();
  const argText = rest.join(' ').trim();

  try {
    if (cmd === 'voices') {
      const { data } = await axios.get(`${API}/voices`, { timeout: 30000, headers: HEADERS });
      await sock.sendMessage(from, { text: `🎙️ Kokoro voices:\n${data.voices.join(', ')}` }, { quoted: msg });
      return true;
    }

    if (cmd === 'tts' || cmd === 'ttsaudio') {
      if (!argText) {
        await sock.sendMessage(from, { text: 'Usage: -tts Hello, this is Kokoro\nYa: -tts af_bella | Hello' }, { quoted: msg });
        return true;
      }
      let voice = DEFAULT_VOICE, text = argText;
      if (argText.includes('|')) {
        const [v, t] = argText.split('|').map(s => s.trim());
        if (/^[a-z]{2}_[a-z]+$/.test(v)) { voice = v; text = t; }
      }
      await sock.sendMessage(from, { text: '🎙️ Generating voice…' }, { quoted: msg });
      const audio = await kokoroTTS(text, voice, 'ogg');

      if (cmd === 'tts') {
        // PTT voice note: Baileys needs OGG/Opus + ptt:true + mimetype
        await sock.sendMessage(from, {
          audio, mimetype: 'audio/ogg; codecs=opus', ptt: true,
        }, { quoted: msg });
      } else {
        await sock.sendMessage(from, {
          audio, mimetype: 'audio/ogg; codecs=opus', ptt: false,
          fileName: 'kokoro-tts.ogg',
        }, { quoted: msg });
      }
      return true;
    }
  } catch (e) {
    await sock.sendMessage(from, { text: `❌ Kokoro TTS failed: ${e.response?.data?.detail || e.message}\nCheck: service chal raha hai? ${API}/health` }, { quoted: msg });
    return true;
  }
  return false;
}

// ADAPT: if your bot loader expects { command, handler } objects, this fits most ABIX loaders.
// Otherwise call handleKokoro(sock, msg) at the top of your main message handler.
module.exports = {
  name: 'kokoro-tts',
  commands: ['tts', 'ttsaudio', 'voices'],
  handleKokoro,
  kokoroTTS,
  handler: handleKokoro,
};
