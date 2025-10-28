@echo off
REM Set UTF-8 encoding for Windows console
chcp 65001 >nul 2>&1

REM Set Python UTF-8 mode
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1

REM Run Django server
python manage.py runserver

pause
