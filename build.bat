@echo off
echo Jira Monitor - EXE Olusturucu
echo ================================

:: venv yoksa olustur
if not exist ".venv\Scripts\activate.bat" (
    echo Virtual environment olusturuluyor...
    python -m venv .venv
)

call .venv\Scripts\activate.bat

:: PyInstaller kur
echo PyInstaller kuruluyor...
pip install pyinstaller -q

:: EXE olustur
echo EXE olusturuluyor...
pyinstaller --onefile --windowed --name "JiraMonitor" --clean monitor.py

echo.
echo Tamamlandi! EXE dosyasi: dist\JiraMonitor.exe
pause
