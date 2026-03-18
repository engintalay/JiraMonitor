@echo off
if not exist ".venv\Scripts\activate.bat" (
    echo Virtual environment bulunamadi. Once install\install.bat calistirin.
    pause
    exit /b 1
)

call .venv\Scripts\activate.bat
python monitor.py
