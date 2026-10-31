"""
Telegram + Kokoro TTS — YES, direct integration works.

Setup:
  pip install python-telegram-bot requests
  set TELEGRAM_BOT_TOKEN=xxxx   (from @BotFather)
  set KOKORO_API=http://127.0.0.1:8880   (the service in ../service/)
  python bot.py

Commands:
  /start          help
  /tts <text>     voice note (OGG/Opus via send_voice)
  /voice af_bella then /tts ...  — or inline: /tts af_bella | Hello
  /voices         list voices
  Any plain text message -> also converted to voice (toggle with /plain on|off)
"""
import os, io, requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

API = os.getenv("KOKORO_API", "http://127.0.0.1:8880")
TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
user_voice = {}   # chat_id -> voice
plain_tts = {}    # chat_id -> bool (default True)

HEADERS = {"x-api-key": os.environ["KOKORO_API_KEY"]} if os.getenv("KOKORO_API_KEY") else {}

def call_tts(text: str, voice: str) -> bytes:
    r = requests.post(f"{API}/tts", json={"text": text, "voice": voice, "format": "ogg"}, headers=HEADERS, timeout=120)
    r.raise_for_status()
    return r.content

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Kokoro TTS ready 🎙️\n"
        "/tts Hello, this is Kokoro speaking\n"
        "/tts af_bella | British female voice example\n"
        "/voices — list all voices\n"
        "Ya bas text bhejo, voice note ban jayega."
    )

async def voices(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    v = requests.get(f"{API}/voices", headers=HEADERS, timeout=30).json()["voices"]
    await update.message.reply_text("Voices:\n" + ", ".join(v))

async def tts_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    raw = " ".join(ctx.args) if ctx.args else ""
    if not raw:
        await update.message.reply_text("Usage: /tts <text>  ya  /tts af_bella | <text>")
        return
    voice = user_voice.get(update.effective_chat.id, "af_heart")
    text = raw
    if "|" in raw:
        maybe_voice, text = raw.split("|", 1)
        maybe_voice, text = maybe_voice.strip(), text.strip()
        if "_" in maybe_voice and len(maybe_voice) <= 20:
            voice = maybe_voice
    await do_voice(update, text, voice)

async def do_voice(update: Update, text: str, voice: str):
    msg = await update.message.reply_text("Generating…")
    try:
        audio = call_tts(text, voice)
        # Telegram voice notes MUST be OGG/Opus — service already returns that
        await update.message.reply_voice(voice=io.BytesIO(audio))
    except Exception as e:
        await update.message.reply_text(f"TTS failed: {e}")
    finally:
        try: await msg.delete()
        except Exception: pass

async def plain(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not plain_tts.get(update.effective_chat.id, True):
        return
    await do_voice(update, update.message.text, user_voice.get(update.effective_chat.id, "af_heart"))

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("tts", tts_cmd))
    app.add_handler(CommandHandler("voices", voices))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, plain))
    print("Telegram Kokoro bot polling…")
    app.run_polling()

if __name__ == "__main__":
    main()
