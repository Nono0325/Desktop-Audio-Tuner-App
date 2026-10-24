@echo off
chcp 65001 >nul
title Desktop Audio Tuner Pro
cd /d "%~dp0"

echo [Desktop Audio Tuner Pro] 正在啟動電腦音質優化與等化器調音器...
python main.py
if errorlevel 1 (
    echo.
    echo 啟動失敗，請確認已安裝 Python 與相關套件。
    echo 正在嘗試安裝相依套件...
    pip install -r requirements.txt
    python main.py
    pause
)
