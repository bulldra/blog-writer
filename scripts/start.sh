#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
cd "$ROOT_DIR"

API_HOST=${API_HOST:-127.0.0.1}
API_PORT=${API_PORT:-8000}

if ! command -v uv >/dev/null 2>&1; then
  echo "[start] uv が見つかりません。https://docs.astral.sh/uv/ を参照してインストールしてください" >&2
  exit 1
fi

if [[ -f "$ROOT_DIR/uv.lock" ]]; then
  echo "[start] uv sync --frozen"
  uv sync --frozen >/dev/null
fi

if [[ -d "$ROOT_DIR/web" ]]; then
  pushd "$ROOT_DIR/web" >/dev/null
  echo "[start] npm ci && npm run build (web)"
  npm ci --silent
  npm run -s build
  popd >/dev/null
fi

echo "[start] API -> http://$API_HOST:$API_PORT"
exec uv run fastapi run app/main.py --host "$API_HOST" --port "$API_PORT"
