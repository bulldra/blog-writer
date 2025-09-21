#!/usr/bin/env bash
set -euo pipefail

killall -q -9 -v -m "uvicorn app.main:app" 2>/dev/null || true
killall -q -9 -v -m "node.*next.*dev" 2>/dev/null || true
killall -q -9 -v -m "npm run -s dev" 2>/dev/null || true
echo "stopped"
