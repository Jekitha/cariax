@echo off
title CARIAX Server
echo ========================================
echo    CARIAX - AI Career Guidance System
echo ========================================
echo.

:: Kill any existing processes
taskkill /F /IM python.exe 2>nul
taskkill /F /IM cloudflared.exe 2>nul
timeout /t 2 /nobreak >nul

:: Start Flask server in background
echo Starting Flask server...
start "CARIAX Flask Server" /min cmd /c "cd /d c:\Users\jekit\Desktop\career\web && python app.py"

:: Wait for Flask to start
timeout /t 3 /nobreak >nul

:: Start Cloudflare tunnel
echo Starting Cloudflare tunnel...
echo.
echo ========================================
echo    PUBLIC URL WILL APPEAR BELOW
echo ========================================
echo.
"C:\Program Files (x86)\cloudflared\cloudflared.exe" tunnel --no-autoupdate --url http://localhost:5000

pause
