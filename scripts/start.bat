@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0.."
set "ROOT=%CD%"
set "LOGS=%ROOT%\scripts\logs"
set "PY=%ROOT%\backend\.venv\Scripts\python.exe"
set "NOBROWSER=0"
if /i "%~1"=="--no-browser" set "NOBROWSER=1"
if not exist "%LOGS%" mkdir "%LOGS%"

title JD Demo 一键启动
echo ============================================================
echo    JD Demo - 京东版式还原演示项目  一键启动
echo ============================================================
echo.

echo [1/7] 检查运行环境
call :need python "Python 3.12+"
call :need node "Node.js 18+"
call :need npm "npm"
echo.

echo [2/7] 准备前端与后端依赖（已安装则跳过）
if not exist "%PY%" (
    echo    - 创建 Python 虚拟环境 backend\.venv ...
    python -m venv "%ROOT%\backend\.venv"
    if errorlevel 1 (
        echo    [失败] 虚拟环境创建失败，请确认 Python 安装完整
        goto :die
    )
    "%PY%" -m pip install --upgrade pip --quiet
)
if exist "%ROOT%\backend\.venv\.deps_ok" (
    echo    - Python 依赖已安装，跳过
) else (
    echo    - 安装 requirements.txt ...
    "%PY%" -m pip install -r "%ROOT%\requirements.txt"
    if errorlevel 1 (
        echo    [失败] Python 依赖安装失败，请检查网络或 pip 源
        goto :die
    )
    echo ok> "%ROOT%\backend\.venv\.deps_ok"
)

if exist "%ROOT%\web\node_modules" (
    echo    - 买家端依赖已安装，跳过
) else (
    echo    - 安装买家端依赖 web\node_modules ...
    pushd "%ROOT%\web"
    call npm install --no-audit --no-fund
    set "RC=!ERRORLEVEL!"
    popd
    if not "!RC!"=="0" (
        echo    [失败] 买家端 npm install 失败
        goto :die
    )
)

if exist "%ROOT%\admin\node_modules" (
    echo    - 后台端依赖已安装，跳过
) else (
    echo    - 安装后台端依赖 admin\node_modules ...
    pushd "%ROOT%\admin"
    call npm install --no-audit --no-fund
    set "RC=!ERRORLEVEL!"
    popd
    if not "!RC!"=="0" (
        echo    [失败] 后台端 npm install 失败
        goto :die
    )
)
echo.

echo [3/7] 检查后端配置 backend\.env
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
    echo    - 数据库模式：MySQL，开始检查并创建数据库
    "%PY%" "%ROOT%\scripts\init_db.py"
    if errorlevel 1 (
        echo    [失败] 数据库初始化失败，请按上面的提示修改 backend\.env
        goto :die
    )
) else (
    echo    - 数据库模式：SQLite（无需建库，开箱即用）
)
echo.

echo [4/7] 同步数据库结构与演示数据
pushd "%ROOT%\backend"
"%PY%" manage.py migrate --noinput
set "RC=!ERRORLEVEL!"
if not "!RC!"=="0" (
    popd
    echo    [失败] 数据库迁移失败，请查看上方报错
    goto :die
)
"%PY%" manage.py seed_demo
set "RC=!ERRORLEVEL!"
popd
if not "!RC!"=="0" (
    echo    [失败] 演示数据生成失败，请查看上方报错
    goto :die
)
echo.

echo [5/7] 检查端口占用
call :need_port 8000 "Django 后端"
if errorlevel 1 goto :port_busy
call :need_port 5173 "买家端"
if errorlevel 1 goto :port_busy
call :need_port 5174 "后台端"
if errorlevel 1 goto :port_busy
echo    - 8000 / 5173 / 5174 均可用
echo.

echo [6/7] 启动三个服务（各自独立窗口，日志写入 scripts\logs）
start "JD-Django :8000" /D "%ROOT%\scripts" cmd /c serve_django.bat
start "JD-Web :5173" /D "%ROOT%\scripts" cmd /c serve_web.bat
start "JD-Admin :5174" /D "%ROOT%\scripts" cmd /c serve_admin.bat
echo    - 已启动，等待端口就绪 ...
echo.

echo [7/7] 等待服务就绪（最多 30 秒）
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
if %TRIES% GEQ 30 goto :not_ready
ping -n 2 127.0.0.1 >nul
goto :wait_loop

:ready
if "%NOBROWSER%"=="1" (
    echo    - 三个服务已就绪（已跳过打开浏览器）
) else (
    echo    - 三个服务已就绪，正在打开浏览器 ...
    start "" http://localhost:5173
)
echo.
call :banner_accounts
echo.
echo  本窗口 20 秒后自动关闭（服务窗口保持运行，停止请双击 scripts\stop.bat）
timeout /t 20 /nobreak >nul
exit /b 0

:port_busy
echo.
echo   [失败] 端口被占用，启动已中止。请先执行 scripts\stop.bat 关闭旧进程，
echo          或手动结束占用端口的程序后重试。
echo.
pause
exit /b 1

:not_ready
echo.
echo   [警告] 30 秒内仍有服务未就绪，请依次检查：
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
:need
where %~1 >nul 2>nul
if errorlevel 1 (
    echo    [失败] 未检测到 %~1，请先安装 %~2 后重试
    goto :die
)
for /f "delims=" %%v in ('%~1 --version 2^>nul') do (
    echo    - %~2 : %%v
    goto :need_done
)
:need_done
exit /b 0

:need_port
netstat -ano | findstr /C:":%~1 " | findstr /C:"LISTENING" >nul
if errorlevel 1 exit /b 0
echo    [占用] 端口 %~1 已被占用（%~2 无法启动）
exit /b 1

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
echo    恢复数据  cd backend ^&^& .venv\Scripts\python.exe manage.py reset_demo --yes
echo ============================================================
exit /b 0
