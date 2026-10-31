@echo off
REM Kokoro TTS - Windows Install (Python 3.10 recommended)
REM Step 1: Python 3.10 install karo https://www.python.org/downloads/release/python-31011/
REM         Installer me "Add python.exe to PATH" lazmi tick karna
REM Step 2: Agar PATH tick bhool gaye to: Settings > Environment Variables > Path > Add:
REM         C:\Users\<you>\AppData\Local\Programs\Python\Python310\
REM         C:\Users\<you>\AppData\Local\Programs\Python\Python310\Scripts\
REM Step 3: Verify (new CMD kholo):
python --version
pip --version
if %errorlevel% neq 0 ( echo Python PATH me nahi mila - Step 2 dobara dekho & exit /b 1 )

echo [1/4] venv bana raha hoon...
python -m venv .venv
call .venv\Scripts\activate.bat

echo [2/4] pip upgrade + CPU torch (Intel CPU ke liye)...
python -m pip install --upgrade pip
pip install torch --index-url https://download.pytorch.org/whl/cpu

echo [3/4] Kokoro + service deps...
pip install -r service\requirements.txt
pip install python-telegram-bot requests

echo [4/4] espeak-ng check (Kokoro ko chahiye)...
where espeak-ng >nul 2>nul || echo WARNING: espeak-ng install karo: https://github.com/espeak-ng/espeak-ng/releases  (MSI installer, PATH auto add hota hai)
where ffmpeg >nul 2>nul || echo WARNING: ffmpeg install karo: https://www.gyan.dev/ffmpeg/builds/  (WhatsApp/Telegram OGG conversion ke liye lazmi)

echo.
echo DONE. Test:  python examples\test_local.py
echo Service:     .venv\Scripts\uvicorn.exe service.app:app --port 8880  (ya service folder se)
pause
