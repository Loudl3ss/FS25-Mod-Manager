#!/usr/bin/env bash
# FS25 Manager — quick launcher
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$SCRIPT_DIR/.venv"

if [ ! -f "$VENV/bin/python" ]; then
    echo "Virtual environment not found. Running setup first..."
    bash "$SCRIPT_DIR/setup.sh"
fi

exec "$VENV/bin/python" "$SCRIPT_DIR/main.py" "$@"
