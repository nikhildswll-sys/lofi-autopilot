@echo off
title Autopilot - Generate 4 Trending Lo-Fi Videos
cd /d "%~dp0"
echo =======================================================
echo   GENERATING 4 TRENDING SLOWED+REVERB VIDEOS NOW...
echo   (No Google API / No Login Needed)
echo =======================================================
echo.
python generate_4_videos.py
echo.
echo =======================================================
echo Check folder: D:\lofi-autopilot\ready_to_upload
echo =======================================================
pause
