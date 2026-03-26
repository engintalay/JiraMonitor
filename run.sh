#!/bin/bash
if [ ! -f ".venv/bin/activate" ]; then
    echo "Virtual environment bulunamadi. Once install/install.sh calistirin."
    exit 1
fi

source .venv/bin/activate
https_proxy="" python3 monitor.py
