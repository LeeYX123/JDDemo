@echo off
rem 排查用启动器：执行 start.bat 后保留窗口，方便查看完整输出与报错
title JD Demo 调试启动
cd /d "%~dp0.."
call scripts\start.bat %*
echo.
echo ============================================================
echo    start.bat 已结束，窗口保留供排查
echo    日志目录：scripts\logs\
echo ============================================================
pause
