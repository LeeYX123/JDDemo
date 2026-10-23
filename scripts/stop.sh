#!/usr/bin/env bash
# JD Demo 停止脚本（macOS / Linux）
set -uo pipefail

echo "============================================================"
echo "    正在停止 JD Demo 的三个服务 ..."
echo "============================================================"

FOUND=0
for port in 8000 5173 5174; do
  pids="$(lsof -iTCP:"$port" -sTCP:LISTEN -t 2>/dev/null || true)"
  if [ -n "$pids" ]; then
    # shellcheck disable=SC2086
    kill -9 $pids 2>/dev/null || true
    echo "    - 已结束端口 $port 的进程 $pids"
    FOUND=1
  fi
done

echo
if [ "$FOUND" = "0" ]; then
  echo "    未发现占用 8000 / 5173 / 5174 的进程，服务可能已经停止。"
else
  echo "    服务已全部停止。"
fi
echo
