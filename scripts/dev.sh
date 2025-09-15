#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
cd "$ROOT_DIR"

API_HOST=${API_HOST:-127.0.0.1}
# 常に 8000 / 3000 を優先的に使用
API_PORT=8000
WEB_PORT=3000

is_busy() {
  local port=$1
  lsof -iTCP:${port} -sTCP:LISTEN -t >/dev/null 2>&1
}

kill_port() {
  local port=$1
  local name=$2
  local pids
  pids=$(lsof -iTCP:${port} -sTCP:LISTEN -t || true)
  if [[ -n "$pids" ]]; then
    echo "[dev] ${name} port ${port} is busy by PIDs: ${pids}. Stopping..."
    kill $pids 2>/dev/null || true
    sleep 1
  fi
  # 強制終了が必要な場合
  if is_busy "$port"; then
    pids=$(lsof -iTCP:${port} -sTCP:LISTEN -t || true)
    if [[ -n "$pids" ]]; then
      kill -9 $pids 2>/dev/null || true
      sleep 1
    fi
  fi
}

ensure_free() {
  local port=$1
  local name=$2
  if is_busy "$port"; then
    kill_port "$port" "$name"
  fi
  if is_busy "$port"; then
    echo "[dev] failed to free ${name} port ${port}" >&2
    exit 1
  fi
}

# 競合時は該当ポートを開放してから固定ポートで起動
ensure_free "$API_PORT" "API"
ensure_free "$WEB_PORT" "Web"

echo "[dev] root = $ROOT_DIR"

if ! command -v uv >/dev/null 2>&1; then
  echo "[dev] uv が見つかりません。https://docs.astral.sh/uv/ を参照してインストールしてください" >&2
  exit 1
fi

# Python 依存の同期（ロックファイルがある場合は凍結）
if [[ -f "$ROOT_DIR/uv.lock" ]]; then
  echo "[dev] uv sync --frozen"
  uv sync --frozen >/dev/null
fi

# Node 依存の準備
if [[ -d "$ROOT_DIR/web" ]]; then
  pushd "$ROOT_DIR/web" >/dev/null
  if [[ ! -d node_modules ]]; then
    echo "[dev] npm ci (web)"
    npm ci --silent
  fi
  popd >/dev/null
fi

cleanup() {
  echo "[dev] stopping..."
  # 親だけでなくリロードで派生した子プロセスも含めて同一PGIDにシグナルを送る
  if [[ -n "${API_PID:-}" ]]; then
    kill -TERM -${API_PID} 2>/dev/null || true
    sleep 1
    kill -KILL -${API_PID} 2>/dev/null || true
  fi
  if [[ -n "${WEB_PID:-}" ]]; then
    kill -TERM -${WEB_PID} 2>/dev/null || true
    sleep 1
    kill -KILL -${WEB_PID} 2>/dev/null || true
  fi
}
trap cleanup INT TERM EXIT

echo "[dev] API -> http://$API_HOST:$API_PORT"
uv run fastapi run app/main.py --host "$API_HOST" --port "$API_PORT" --reload &
API_PID=$!

if [[ -d "$ROOT_DIR/web" ]]; then
  echo "[dev] Web -> http://localhost:$WEB_PORT (API_BASE=http://$API_HOST:$API_PORT)"
  (cd "$ROOT_DIR/web" \
    && NEXT_PUBLIC_API_BASE="http://$API_HOST:$API_PORT" PORT="$WEB_PORT" npm run -s dev) &
  WEB_PID=$!
else
  echo "[dev] web ディレクトリが無いためフロントは起動しません"
fi

wait
