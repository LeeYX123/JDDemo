#!/usr/bin/env bash
# JD Demo 一键启动（macOS / Linux）
# 幂等：重复执行不会重复安装依赖、不会重复造数
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOGS="$ROOT/scripts/logs"
PY="$ROOT/backend/.venv/bin/python"
mkdir -p "$LOGS"

info() { printf '    - %s\n' "$1"; }
fail() { printf '\n    [失败] %s\n\n' "$1"; exit 1; }

echo "============================================================"
echo "    JD Demo - 京东版式还原演示项目  一键启动"
echo "============================================================"

echo "[1/7] 检查运行环境"
command -v python3 >/dev/null 2>&1 || fail "未检测到 python3，请先安装 Python 3.12+"
command -v node >/dev/null 2>&1 || fail "未检测到 node，请先安装 Node.js 18+"
command -v npm >/dev/null 2>&1 || fail "未检测到 npm，请先安装 Node.js 18+"
info "python3: $(python3 --version 2>&1)"
info "node: $(node --version 2>&1)"
info "npm: $(npm --version 2>&1)"

echo "[2/7] 准备依赖（已安装则跳过）"
if [ ! -x "$PY" ]; then
  info "创建虚拟环境 backend/.venv"
  python3 -m venv "$ROOT/backend/.venv" || fail "虚拟环境创建失败"
  "$PY" -m pip install --upgrade pip --quiet
fi
if [ -f "$ROOT/backend/.venv/.deps_ok" ]; then
  info "Python 依赖已安装"
else
  info "安装 requirements.txt"
  "$PY" -m pip install -r "$ROOT/requirements.txt" || fail "Python 依赖安装失败"
  : > "$ROOT/backend/.venv/.deps_ok"
fi

for app in web admin; do
  if [ -d "$ROOT/$app/node_modules" ]; then
    info "$app 依赖已安装"
  else
    info "安装 $app 依赖"
    (cd "$ROOT/$app" && npm install --no-audit --no-fund) || fail "$app npm install 失败"
  fi
done

echo "[3/7] 检查后端配置 backend/.env"
if [ ! -f "$ROOT/backend/.env" ]; then
  cp "$ROOT/backend/.env.example" "$ROOT/backend/.env"
  cat <<'EOF'

    [提示] 已生成 backend/.env
    默认使用 SQLite，可直接演示；若要用 MySQL 请修改：
      DB_ENGINE=mysql
      DB_USER=root
      DB_PASSWORD=你的密码
    修改后重新运行 scripts/start.sh
EOF
  exit 0
fi

DB_ENGINE="$(grep -E '^DB_ENGINE=' "$ROOT/backend/.env" | head -1 | cut -d= -f2 | tr -d ' \r')"
DB_ENGINE="${DB_ENGINE:-sqlite}"
if [ "$DB_ENGINE" = "mysql" ]; then
  info "数据库模式：MySQL"
  "$PY" "$ROOT/scripts/init_db.py" || fail "数据库初始化失败，请检查 backend/.env"
else
  info "数据库模式：SQLite"
fi

echo "[4/7] 同步数据库结构与演示数据"
(cd "$ROOT/backend" && "$PY" manage.py migrate --noinput) || fail "数据库迁移失败"
(cd "$ROOT/backend" && "$PY" manage.py seed_demo) || fail "演示数据生成失败"

echo "[5/7] 检查端口占用"
port_busy() { lsof -iTCP:"$1" -sTCP:LISTEN -t >/dev/null 2>&1; }
for port in 8000 5173 5174; do
  if port_busy "$port"; then
    fail "端口 $port 已被占用，请先执行 scripts/stop.sh 或结束占用进程"
  fi
done
info "8000 / 5173 / 5174 均可用"

echo "[6/7] 启动三个服务（后台运行，日志写入 scripts/logs）"
(cd "$ROOT/backend" && nohup "$PY" manage.py runserver 127.0.0.1:8000 >> "$LOGS/django.log" 2>&1 &)
(cd "$ROOT/web" && nohup npm run dev >> "$LOGS/web.log" 2>&1 &)
(cd "$ROOT/admin" && nohup npm run dev >> "$LOGS/admin.log" 2>&1 &)
info "已启动，等待端口就绪"

echo "[7/7] 等待服务就绪（最多 30 秒）"
for _ in $(seq 1 30); do
  if port_busy 8000 && port_busy 5173 && port_busy 5174; then
    ready=1
    break
  fi
  sleep 1
done
if [ "${ready:-0}" != "1" ]; then
  printf '\n    [警告] 30 秒内仍有服务未就绪，请检查 scripts/logs/ 下的三个日志\n\n'
  exit 1
fi

cat <<'EOF'

============================================================
   演示账号（密码均为 123456）
------------------------------------------------------------
   买家  13800138000    http://localhost:5173
   商家  13900139000    http://localhost:5174/merchant
   平台  13700137000    http://localhost:5174/console
------------------------------------------------------------
   买家端   http://localhost:5173
   后台端   http://localhost:5174
   接口     http://127.0.0.1:8000/api/v1/
   恢复数据 backend/.venv/bin/python manage.py reset_demo --yes
============================================================

EOF

if command -v open >/dev/null 2>&1; then
  open http://localhost:5173
elif command -v xdg-open >/dev/null 2>&1; then
  xdg-open http://localhost:5173 >/dev/null 2>&1 &
fi
