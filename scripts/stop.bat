@echo off
setlocal EnableExtensions EnableDelayedExpansion
title JD Demo 停止服务
echo ============================================================
echo    正在停止 JD Demo 的三个服务 ...
echo ============================================================

set "FOUND=0"
for %%P in (8000 5173 5174) do (
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr /C:":%%P " ^| findstr /C:"LISTENING"') do (
        if not "%%a"=="0" (
            taskkill /F /T /PID %%a >nul 2>nul
            if not errorlevel 1 (
                echo    - 已结束端口 %%P 的进程 %%a
                set "FOUND=1"
            )
        )
    )
)

taskkill /F /FI "WINDOWTITLE eq JD-Django*" >nul 2>nul
taskkill /F /FI "WINDOWTITLE eq JD-Web*" >nul 2>nul
taskkill /F /FI "WINDOWTITLE eq JD-Admin*" >nul 2>nul

echo.
if "%FOUND%"=="0" (
    echo    未发现占用 8000 / 5173 / 5174 的进程，服务可能已经停止。
) else (
    echo    服务已全部停止。
)
echo.
pause
exit /b 0
