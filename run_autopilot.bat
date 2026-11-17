@echo off
title YouTube Autopilot - Daily 4 Videos Runner
cd /d "%~dp0"
echo =======================================================
echo   STARTING AUTOPILOT (DAILY 4 LO-FI VIDEOS)
echo =======================================================
echo.
python autopilot.py
echo.
echo Process complete!
pause
