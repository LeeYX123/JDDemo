@echo off
rem 内部启动器：Django 后端（由 start.bat 调用，也可单独运行）
cd /d "%~dp0..\backend"
if not exist "%~dp0logs" mkdir "%~dp0logs"
echo [start] Django runserver 127.0.0.1:8000 >> "%~dp0logs\django.log"
".venv\Scripts\python.exe" manage.py runserver 127.0.0.1:8000 >> "%~dp0logs\django.log" 2>&1
echo.
echo Django 进程已退出，请查看 scripts\logs\django.log 排查原因。
pause
