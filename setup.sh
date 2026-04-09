#!/usr/bin/env bash
# FS25 Manager — setup script for Bazzite / GNOME
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$SCRIPT_DIR/.venv"

echo "==> Creating Python virtual environment..."
python3 -m venv "$VENV"

echo "==> Installing dependencies..."
"$VENV/bin/pip" install --upgrade pip --quiet
"$VENV/bin/pip" install PyQt6>=6.4.0 --quiet

echo "==> Writing desktop entry..."
DESKTOP_DIR="$HOME/.local/share/applications"
mkdir -p "$DESKTOP_DIR"
cat > "$DESKTOP_DIR/fs25-manager.desktop" <<EOF
[Desktop Entry]
Name=FS25 Manager
Comment=Manage Farming Simulator 25 mods and saves on Linux
Exec=$VENV/bin/python $SCRIPT_DIR/main.py
Icon=applications-games
Terminal=false
Type=Application
Categories=Game;Utility;
Keywords=farming;simulator;mods;fs25;
EOF

echo ""
echo "✅ Setup complete!"
echo ""
echo "Run the app with:"
echo "    $VENV/bin/python $SCRIPT_DIR/main.py"
echo ""
echo "Or use the app launcher in your GNOME app grid: 'FS25 Manager'"
