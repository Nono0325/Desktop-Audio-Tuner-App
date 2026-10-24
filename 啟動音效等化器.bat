@echo off
chcp 65001 >nul
title Desktop Audio Tuner Pro
cd /d "%~dp0"

echo [Desktop Audio Tuner Pro] 正在啟動電腦音質優化與等化器調音器...

set "PYTHON_EXE=C:\Users\hungr\anaconda3\python.exe"
if not exist "%PYTHON_EXE%" (
    set "PYTHON_EXE=python.exe"
)

"%PYTHON_EXE%" main.py
if errorlevel 1 (
    echo.
    echo 啟動發生錯誤，請查看上方訊息。
    pause
)
