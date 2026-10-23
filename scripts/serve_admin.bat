@echo off
rem 内部启动器：后台端 Vite dev server（5174）
cd /d "%~dp0..\admin"
if not exist "%~dp0logs" mkdir "%~dp0logs"
echo [start] admin dev server 5174 >> "%~dp0logs\admin.log"
call npm run dev >> "%~dp0logs\admin.log" 2>&1
echo.
echo 后台端进程已退出，请查看 scripts\logs\admin.log 排查原因。
pause
