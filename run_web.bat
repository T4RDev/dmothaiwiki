@echo off
chcp 65001 >nul
title Digimon Thai Wiki - Web Server (100% Offline)

echo =======================================================
echo   🦖 DIGIMON THAI WIKI - OFFLINE WEB APPLICATION 🦖
echo =======================================================
echo.
echo กำลังค้นหา Python ในเครื่อง...

set PYTHON_CMD=python
where python >nul 2>nul
if %errorlevel% neq 0 (
    if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
        set PYTHON_CMD="%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    ) else (
        echo [ERROR] ไม่พบ Python ในเครื่อง กรุณาติดตั้ง Python 3.10+
        pause
        exit /b 1
    )
)

echo กำลังเริ่มรันเซิร์ฟเวอร์ Digimon Thai Wiki...
echo URL: http://localhost:8000
echo.
start "" http://localhost:8000

%PYTHON_CMD% web\server.py

pause

