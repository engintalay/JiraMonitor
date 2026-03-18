#!/bin/bash
echo "Jira Monitor - Kurulum"
echo "========================"

# Python kontrolü
if ! command -v python3 &> /dev/null; then
    echo "HATA: Python3 bulunamadi. Lutfen Python 3.8+ yukleyin."
    exit 1
fi

# tkinter kontrolü
python3 -c "import tkinter" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "HATA: tkinter bulunamadi."
    echo "Ubuntu/Debian: sudo apt-get install python3-tk"
    echo "Fedora/RHEL:   sudo dnf install python3-tkinter"
    echo "macOS:         brew install python-tk"
    exit 1
fi

# Virtual env oluştur
echo "Virtual environment olusturuluyor..."
python3 -m venv .venv

echo "Kurulum tamamlandi."
echo "Uygulamayi calistirmak icin: ./run.sh"
