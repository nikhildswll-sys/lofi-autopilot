@echo off
title YouTube Autopilot - 1-Time Google Sign-In
cd /d "%~dp0"
echo =======================================================
echo   1-TIME YOUTUBE ACCOUNT AUTHORIZATION
echo =======================================================
echo.
echo Browser khulega, apna YouTube channel wala Google account select karein
echo aur "Allow" dabayein taaki token.json ban sake!
echo.
python login.py
echo.
pause
