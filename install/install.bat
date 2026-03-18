@echo off
echo Jira Monitor - Kurulum
echo ========================

:: Python kontrolü
python --version >nul 2>&1
if errorlevel 1 (
    echo HATA: Python bulunamadi. Lutfen Python 3.8+ yukleyin.
    pause
    exit /b 1
)

:: Virtual env oluştur
echo Virtual environment olusturuluyor...
python -m venv .venv

:: Aktifleştir ve tkinter kontrolü
call .venv\Scripts\activate.bat

echo Kurulum tamamlandi.
echo Uygulamayi calistirmak icin: run.bat
pause
