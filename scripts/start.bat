@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0.."
set "ROOT=%CD%"
set "LOGS=%ROOT%\scripts\logs"
set "VENV_PY=%ROOT%\backend\.venv\Scripts\python.exe"
set "NOBROWSER=0"
set "REPAIR="
set "FORCEENV="

:parse_args
if "%~1"=="" goto :args_done
if /i "%~1"=="--no-browser" set "NOBROWSER=1"
if /i "%~1"=="--repair" set "REPAIR=--repair"
if /i "%~1"=="--force-env" set "FORCEENV=1"
shift
goto :parse_args
:args_done

if not exist "%LOGS%" mkdir "%LOGS%"

title JD Demo 一键启动
echo ============================================================
echo    JD Demo - 京东版式还原演示项目  一键启动
echo ============================================================
echo.

echo [1/7] 检查运行环境（缺失或版本过低会自动下载安装）
set "PSEXE="
if exist "%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" set "PSEXE=%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe"
if not defined PSEXE for /f "delims=" %%p in ('where powershell 2^>nul') do if not defined PSEXE set "PSEXE=%%p"
if not defined PSEXE (
    echo    [失败] 未找到 PowerShell，无法自动准备运行环境
    echo          请手动安装 Python 3.10+ 与 Node.js 18+ 后重试
    goto :die
)
if defined FORCEENV (
    "%PSEXE%" -NoProfile -ExecutionPolicy Bypass -File "%ROOT%\scripts\bootstrap.ps1" -Root "%ROOT%" -ForceNode -ForcePython
) else (
    "%PSEXE%" -NoProfile -ExecutionPolicy Bypass -File "%ROOT%\scripts\bootstrap.ps1" -Root "%ROOT%"
)
if errorlevel 1 (
    echo    [失败] 运行环境准备失败
    echo          详细日志：scripts\logs\bootstrap.log
    goto :die
)
if not exist "%LOGS%\env.cmd" (
    echo    [失败] 未生成环境变量文件 scripts\logs\env.cmd
    goto :die
)
call "%LOGS%\env.cmd"
if not defined SYS_PY (
    echo    [失败] 环境变量 SYS_PY 未设置
    goto :die
)
echo.

echo [2/7] 准备虚拟环境与依赖（损坏会自动修复）
"%SYS_PY%" "%ROOT%\scripts\tools\prepare.py" --root "%ROOT%" %REPAIR%
if errorlevel 1 (
    echo    [失败] 依赖准备失败
    echo          可尝试：scripts\start.bat --repair 强制重建
    goto :die
)
echo.

echo [3/7] 检查数据库配置与结构
if not exist "%ROOT%\backend\.env" (
    copy /y "%ROOT%\backend\.env.example" "%ROOT%\backend\.env" >nul
    echo    [提示] 已根据 .env.example 生成 backend\.env
    echo.
    echo    默认使用 SQLite，可直接演示；如需 MySQL 请：
    echo      [1] 用记事本打开 backend\.env
    echo      [2] 把 DB_ENGINE=sqlite 改为 DB_ENGINE=mysql
    echo      [3] 填写 DB_USER 与 DB_PASSWORD
    echo    修改完成后重新双击 start.bat
    echo.
    pause
    exit /b 0
)

set "DB_ENGINE=sqlite"
for /f "tokens=1,* delims==" %%a in ("%ROOT%\backend\.env") do (
    if /i "%%a"=="DB_ENGINE" set "DB_ENGINE=%%b"
)
if /i "%DB_ENGINE%"=="mysql" (
    echo    - 数据库模式：MySQL，检查并创建数据库
    "%VENV_PY%" "%ROOT%\scripts\init_db.py"
    if errorlevel 1 (
        echo    [失败] 数据库初始化失败，请检查 backend\.env 的 MySQL 配置
        goto :die
    )
) else (
    echo    - 数据库模式：SQLite，无需建库
)

pushd "%ROOT%\backend"
"%VENV_PY%" manage.py migrate --noinput
set "RC=!ERRORLEVEL!"
if not "!RC!"=="0" (
    popd
    echo    [失败] 数据库迁移失败，请查看上方报错
    goto :die
)
"%VENV_PY%" manage.py seed_demo
set "RC=!ERRORLEVEL!"
if "!RC!"=="0" "%VENV_PY%" manage.py refresh_demo
popd
if not "!RC!"=="0" (
    echo    [失败] 演示数据生成失败，请查看上方报错
    goto :die
)
echo.

echo [4/7] 检查端口占用（上一轮残留会自动清理）
call :ensure_port 8000 "Django 后端"
if errorlevel 1 goto :port_fail
call :ensure_port 5173 "买家端"
if errorlevel 1 goto :port_fail
call :ensure_port 5174 "后台端"
if errorlevel 1 goto :port_fail
echo.

echo [5/7] 启动三个服务（各自独立窗口，日志写入 scripts\logs）
start "JD-Django :8000" /D "%ROOT%\scripts" cmd /c serve_django.bat
start "JD-Web :5173" /D "%ROOT%\scripts" cmd /c serve_web.bat
start "JD-Admin :5174" /D "%ROOT%\scripts" cmd /c serve_admin.bat
echo    - 已启动，等待端口就绪 ...
echo.

echo [6/7] 等待服务就绪（最多 60 秒）
set /a TRIES=0
:wait_loop
set "UP=1"
netstat -ano | findstr /C:":8000 " | findstr /C:"LISTENING" >nul
if errorlevel 1 set "UP=0"
netstat -ano | findstr /C:":5173 " | findstr /C:"LISTENING" >nul
if errorlevel 1 set "UP=0"
netstat -ano | findstr /C:":5174 " | findstr /C:"LISTENING" >nul
if errorlevel 1 set "UP=0"
if "%UP%"=="1" goto :ready
set /a TRIES+=1
if %TRIES% GEQ 60 goto :not_ready
ping -n 2 127.0.0.1 >nul
goto :wait_loop

:ready
echo    - 三个服务已就绪
echo.
echo [7/7] 启动完成
if "%NOBROWSER%"=="1" (
    echo    - 已跳过打开浏览器（--no-browser）
) else (
    echo    - 正在打开浏览器 ...
    start "" http://localhost:5173
)
echo.
call :banner_accounts
echo.
echo  本窗口 20 秒后自动关闭（服务窗口保持运行，停止请双击 scripts\stop.bat）
timeout /t 20 /nobreak >nul 2>nul
if errorlevel 1 ping -n 21 127.0.0.1 >nul
exit /b 0

:port_fail
echo.
echo   [失败] 端口被其他程序占用，启动已中止。
echo          请关闭占用程序，或先执行 scripts\stop.bat 清理本项目进程后重试。
echo.
pause
exit /b 1

:not_ready
echo.
echo   [警告] 60 秒内仍有服务未就绪，请依次检查：
echo          [1] scripts\logs\django.log
echo          [2] scripts\logs\web.log
echo          [3] scripts\logs\admin.log
echo.
echo   常见原因：依赖未装完、数据库密码错误、端口被其他程序抢占。
echo.
pause
exit /b 1

:die
echo.
echo   启动中止，请按上面的提示处理后重新运行。
echo.
pause
exit /b 1

rem ------------------------------------------------------------------ 子过程
:ensure_port
set "PORT=%~1"
set "PTITLE=%~2"
set "PORT_PID="
for /f "tokens=5" %%p in ('netstat -ano ^| findstr /C:":%PORT% " ^| findstr /C:"LISTENING"') do set "PORT_PID=%%p"
if not defined PORT_PID (
    echo    - 端口 %PORT% 可用
    exit /b 0
)
if "%PORT_PID%"=="0" (
    echo    - 端口 %PORT% 可用
    exit /b 0
)
set "PORT_IMAGE="
for /f "tokens=1 delims=," %%n in ('tasklist /FI "PID eq %PORT_PID%" /FO CSV /NH 2^>nul') do set "PORT_IMAGE=%%~n"
if not defined PORT_IMAGE (
    echo    [提示] 端口 %PORT% 的占用进程（PID %PORT_PID%）已退出，等待系统释放端口
    ping -n 3 127.0.0.1 >nul
    exit /b 0
)
echo    [提示] 端口 %PORT% 被 %PORT_IMAGE% 占用（PID %PORT_PID%），%PTITLE% 需要该端口
echo %PORT_IMAGE% | findstr /I "python.exe node.exe" >nul
if errorlevel 1 (
    echo    [失败] 占用者不是本项目进程，已停止启动
    exit /b 1
)
taskkill /F /T /PID %PORT_PID% >nul 2>nul
ping -n 2 127.0.0.1 >nul
echo    - 已结束上一轮残留的 %PORT_IMAGE%，继续启动
exit /b 0

:banner_accounts
echo ============================================================
echo    演示账号（密码均为 123456）
echo ------------------------------------------------------------
echo    买家  13800138000    http://localhost:5173
echo    商家  13900139000    http://localhost:5174/merchant
echo    平台  13700137000    http://localhost:5174/console
echo ------------------------------------------------------------
echo    买家端   http://localhost:5173
echo    后台端   http://localhost:5174
echo    接口     http://127.0.0.1:8000/api/v1/
echo ------------------------------------------------------------
echo    重建依赖   start.bat --repair
echo    重装环境   start.bat --force-env
echo    恢复数据   cd backend ^&^& .venv\Scripts\python.exe manage.py reset_demo --yes
echo ============================================================
exit /b 0
