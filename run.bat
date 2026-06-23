@echo off
chcp 65001 >nul
cd /d "%~dp0python"
"%~dp0python\venv\Scripts\python.exe" main.py %*
pause
