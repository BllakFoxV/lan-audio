@echo off
cd /d "%~dp0"
python app\gui.py %*
if errorlevel 1 pause
