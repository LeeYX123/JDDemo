@echo off
rem 内部启动器：买家端 Vite dev server（5173）
cd /d "%~dp0..\web"
if not exist "%~dp0logs" mkdir "%~dp0logs"
echo [start] web dev server 5173 >> "%~dp0logs\web.log"
call npm run dev >> "%~dp0logs\web.log" 2>&1
echo.
echo 买家端进程已退出，请查看 scripts\logs\web.log 排查原因。
pause
