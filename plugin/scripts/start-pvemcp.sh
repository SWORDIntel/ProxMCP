#!/usr/bin/env sh
set -eu

ROOT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)"

if [ "${PVEMCP_SERVER_CMD:-}" != "" ]; then
  exec sh -c "$PVEMCP_SERVER_CMD"
fi

if command -v pvemcp-server >/dev/null 2>&1; then
  exec pvemcp-server
fi

if [ -x "$ROOT_DIR/.venv/bin/pvemcp-server" ]; then
  exec "$ROOT_DIR/.venv/bin/pvemcp-server"
fi

if command -v python3 >/dev/null 2>&1; then
  if [ -d "$ROOT_DIR/src" ]; then
    export PYTHONPATH="$ROOT_DIR/src${PYTHONPATH:+:$PYTHONPATH}"
  fi
  exec python3 -m pvemcp.mcp_server
fi

echo "pvemcp: unable to start server (missing pvemcp-server/.venv/python3)" >&2
exit 1
