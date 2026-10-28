#!/usr/bin/env bash
# JD Demo 一键启动（macOS / Linux）
# - 没有 Node / Python 或版本过低时，自动下载便携版本到 .runtime 并复用
# - 虚拟环境损坏、依赖变化、端口残留都会自动修复
# 用法：bash scripts/start.sh [--repair] [--no-browser] [--force-env]
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOGS="$ROOT/scripts/logs"
RUNTIME="$ROOT/.runtime"
CACHE="$RUNTIME/_cache"
NODE_TARGET="22.14.0"
NODE_MIN="18.0.0"
PY_MIN="3.10"
mkdir -p "$LOGS" "$CACHE"

REPAIR=""
NOBROWSER=0
FORCE_ENV=0
for arg in "$@"; do
  case "$arg" in
    --repair) REPAIR="--repair" ;;
    --no-browser) NOBROWSER=1 ;;
    --force-env) FORCE_ENV=1 ;;
  esac
done

info() { printf '   - %s\n' "$1"; }
ok() { printf '   [OK] %s\n' "$1"; }
tip() { printf '   [提示] %s\n' "$1"; }
fail() { printf '\n   [失败] %s\n\n' "$1"; exit 1; }

# 版本比较：$1 >= $2
ver_ge() {
  awk -v a="$1" -v b="$2" 'BEGIN{
    n=split(a,A,"."); m=split(b,B,".");
    for(i=1;i<=3;i++){ if(A[i]+0>B[i]+0) exit 0; if(A[i]+0<B[i]+0) exit 1 }
    exit 0
  }'
}

download() { # $1=url $2=dest
  if command -v curl >/dev/null 2>&1; then
    curl -fL --retry 2 --connect-timeout 20 --max-time 900 -o "$2" "$1" 2>/dev/null
  elif command -v wget >/dev/null 2>&1; then
    wget -q -O "$2" "$1"
  else
    return 1
  fi
}

echo "============================================================"
echo "    JD Demo - 京东版式还原演示项目  一键启动"
echo "============================================================"

echo "[1/7] 检查运行环境（缺失或版本过低会自动下载）"
NODE_BIN=""
NODE_VER=""
find_node() {
  local candidate version
  for candidate in \
    "$(command -v node 2>/dev/null)" \
    /usr/local/bin/node \
    /opt/homebrew/bin/node \
    "$HOME"/.nvm/versions/node/*/bin/node; do
    [ -n "$candidate" ] && [ -x "$candidate" ] || continue
    version="$("$candidate" -v 2>/dev/null | sed 's/^v//')"
    [ -n "$version" ] || continue
    if ver_ge "$version" "$NODE_MIN"; then
      NODE_BIN="$candidate"
      NODE_VER="$version"
      return 0
    fi
  done
  return 1
}

install_node() {
  local os arch triple folder tarball url
  case "$(uname -s)" in
    Darwin) os="darwin" ;;
    Linux) os="linux" ;;
    *) fail "当前系统不受支持，请手动安装 Node.js ${NODE_MIN}+" ;;
  esac
  case "$(uname -m)" in
    arm64|aarch64) arch="arm64" ;;
    x86_64|amd64) arch="x64" ;;
    *) fail "当前架构不受支持，请手动安装 Node.js ${NODE_MIN}+" ;;
  esac
  folder="node-v${NODE_TARGET}-${os}-${arch}"
  tarball="$CACHE/${folder}.tar.gz"
  if [ ! -f "$tarball" ]; then
    info "下载 Node.js v${NODE_TARGET} ..."
    for url in \
      "https://nodejs.org/dist/v${NODE_TARGET}/${folder}.tar.gz" \
      "https://npmmirror.com/mirrors/node/v${NODE_TARGET}/${folder}.tar.gz"; do
      download "$url" "$tarball" && break
    done
    [ -s "$tarball" ] || fail "Node.js 下载失败，请检查网络或手动安装 Node.js ${NODE_MIN}+"
  fi
  info "解压 Node.js ..."
  rm -rf "$RUNTIME/$folder"
  tar -xzf "$tarball" -C "$RUNTIME" || fail "Node.js 解压失败"
  export PATH="$RUNTIME/$folder/bin:$PATH"
  NODE_BIN="$RUNTIME/$folder/bin/node"
  NODE_VER="$("$NODE_BIN" -v | sed 's/^v//')"
  ok "Node.js v${NODE_VER} 已安装到 .runtime/$folder"
}

if [ "$FORCE_ENV" = "1" ] || ! find_node; then
  [ "$FORCE_ENV" = "1" ] || tip "未检测到 Node.js ${NODE_MIN}+"
  install_node
else
  ok "Node.js v${NODE_VER}（${NODE_BIN}）"
fi
export PATH="$(dirname "$NODE_BIN"):$PATH"

SYS_PY=""
find_python() {
  local candidate version
  for candidate in python3.13 python3.12 python3.11 python3.10 python3 python; do
    command -v "$candidate" >/dev/null 2>&1 || continue
    version="$("$candidate" -c 'import sys;print("%d.%d"%sys.version_info[:2])' 2>/dev/null)"
    [ -n "$version" ] || continue
    if ver_ge "$version" "$PY_MIN"; then
      SYS_PY="$(command -v "$candidate")"
      return 0
    fi
  done
  return 1
}

ensure_python() {
  if [ "$FORCE_ENV" != "1" ] && find_python; then
    ok "Python $("$SYS_PY" -c 'import sys;print("%d.%d.%d"%sys.version_info[:3])')（${SYS_PY}）"
    return 0
  fi
  tip "未检测到 Python ${PY_MIN}+，尝试用 uv 安装便携版"
  local uv_bin="$RUNTIME/uv/uv"
  if ! [ -x "$uv_bin" ]; then
    command -v uv >/dev/null 2>&1 && uv_bin="$(command -v uv)"
  fi
  if ! [ -x "$uv_bin" ]; then
    local triple
    case "$(uname -s)-$(uname -m)" in
      Darwin-arm64) triple="aarch64-apple-darwin" ;;
      Darwin-x86_64) triple="x86_64-apple-darwin" ;;
      Linux-aarch64|Linux-arm64) triple="aarch64-unknown-linux-gnu" ;;
      Linux-x86_64) triple="x86_64-unknown-linux-gnu" ;;
      *) fail "无法自动安装 Python，请手动安装 Python ${PY_MIN}+" ;;
    esac
    info "下载 uv ..."
    mkdir -p "$RUNTIME/uv"
    local pkg="$CACHE/uv-${triple}.tar.gz"
    download "https://github.com/astral-sh/uv/releases/latest/download/uv-${triple}.tar.gz" "$pkg" ||
      fail "uv 下载失败，请手动安装 Python ${PY_MIN}+"
    tar -xzf "$pkg" -C "$RUNTIME/uv" --strip-components=1 || fail "uv 解压失败"
    uv_bin="$RUNTIME/uv/uv"
  fi
  info "用 uv 安装 Python 3.12（首次约 1 分钟）..."
  "$uv_bin" python install 3.12 || fail "Python 安装失败，请手动安装 Python ${PY_MIN}+"
  SYS_PY="$("$uv_bin" python find 3.12)"
  [ -n "$SYS_PY" ] || fail "找到不到 uv 安装的 Python"
  ok "Python 已就绪（${SYS_PY}）"
}
ensure_python

echo "[2/7] 准备虚拟环境与依赖（损坏会自动修复）"
"$SYS_PY" "$ROOT/scripts/tools/prepare.py" --root "$ROOT" $REPAIR ||
  fail "依赖准备失败，可尝试 bash scripts/start.sh --repair"

echo "[3/7] 检查数据库配置与结构"
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
PY="$ROOT/backend/.venv/bin/python"
if [ "$DB_ENGINE" = "mysql" ]; then
  info "数据库模式：MySQL"
  "$PY" "$ROOT/scripts/init_db.py" || fail "数据库初始化失败，请检查 backend/.env"
else
  info "数据库模式：SQLite，无需建库"
fi
(cd "$ROOT/backend" && "$PY" manage.py migrate --noinput) || fail "数据库迁移失败"
(cd "$ROOT/backend" && "$PY" manage.py seed_demo) || fail "演示数据生成失败"
(cd "$ROOT/backend" && "$PY" manage.py refresh_demo) || true

echo "[4/7] 检查端口占用（上一轮残留会自动清理）"
port_pid() {
  if command -v lsof >/dev/null 2>&1; then
    lsof -t -iTCP:"$1" -sTCP:LISTEN 2>/dev/null | head -1
  fi
}
for port in 8000 5173 5174; do
  pid="$(port_pid "$port")"
  if [ -z "$pid" ]; then
    info "端口 $port 可用"
    continue
  fi
  name="$(ps -p "$pid" -o comm= 2>/dev/null | xargs basename 2>/dev/null)"
  tip "端口 $port 被 ${name:-未知进程} 占用（PID $pid）"
  case "$name" in
    python*|node*)
      kill -9 "$pid" 2>/dev/null || true
      sleep 1
      info "已结束上一轮残留的 ${name}，继续启动"
      ;;
    *)
      fail "端口 $port 被其他程序占用，请关闭后重试"
      ;;
  esac
done

echo "[5/7] 启动三个服务（后台运行，日志写入 scripts/logs）"
(cd "$ROOT/backend" && nohup "$PY" manage.py runserver 127.0.0.1:8000 >> "$LOGS/django.log" 2>&1 &)
(cd "$ROOT/web" && nohup npm run dev >> "$LOGS/web.log" 2>&1 &)
(cd "$ROOT/admin" && nohup npm run dev >> "$LOGS/admin.log" 2>&1 &)
info "已启动，等待端口就绪"

echo "[6/7] 等待服务就绪（最多 60 秒）"
ready=0
for _ in $(seq 1 60); do
  if [ -n "$(port_pid 8000)" ] && [ -n "$(port_pid 5173)" ] && [ -n "$(port_pid 5174)" ]; then
    ready=1
    break
  fi
  sleep 1
done
[ "$ready" = "1" ] || fail "60 秒内仍有服务未就绪，请检查 scripts/logs/ 下的日志"
ok "三个服务已就绪"

echo "[7/7] 启动完成"
if [ "$NOBROWSER" = "1" ]; then
  info "已跳过打开浏览器（--no-browser）"
elif command -v open >/dev/null 2>&1; then
  open http://localhost:5173
elif command -v xdg-open >/dev/null 2>&1; then
  xdg-open http://localhost:5173 >/dev/null 2>&1 &
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
------------------------------------------------------------
   重建依赖   bash scripts/start.sh --repair
   重装环境   bash scripts/start.sh --force-env
   恢复数据   cd backend && .venv/bin/python manage.py reset_demo --yes
============================================================

EOF
