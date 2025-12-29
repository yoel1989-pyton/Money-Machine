@echo off
REM ============================================================
REM FINVID OMNI - One-Click Video Build (Windows)
REM ============================================================
REM Double-click this file to merge all OPAL clips into final_video.mp4
REM ============================================================

echo.
echo ============================================================
echo   FINVID OMNI - Building Final Video
echo ============================================================
echo.

python merge.py

echo.
echo ============================================================
echo   Done! Check final_video.mp4
echo ============================================================
echo.

pause
