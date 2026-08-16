#!/usr/bin/env bash
# FS25 Manager — build the AppImage into dist/
#
# Usage:
#   ./build-appimage.sh              build at the current version
#   ./build-appimage.sh patch        bug fixes only
#   ./build-appimage.sh minor        new features, backwards compatible
#   ./build-appimage.sh major        breaking changes
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
VENV="$SCRIPT_DIR/.venv"
BUMP="${1:-}"

if [ ! -x "$VENV/bin/python" ]; then
    echo "==> Creating virtual environment..."
    python3 -m venv "$VENV"
fi
"$VENV/bin/pip" install -q --disable-pip-version-check -r requirements.txt pyinstaller

if [ -n "$BUMP" ]; then
    echo "==> Bumping $BUMP version..."
    "$VENV/bin/python" - "$BUMP" <<'PY'
import pathlib, re, sys

bump = sys.argv[1]
if bump not in ("major", "minor", "patch"):
    sys.exit(f"unknown bump '{bump}': use major, minor or patch")

version_file = pathlib.Path("core/version.py")
text = version_file.read_text(encoding="utf-8")
major, minor, patch = (int(n) for n in re.search(r'"(\d+)\.(\d+)\.(\d+)"', text).groups())

if bump == "major":
    major, minor, patch = major + 1, 0, 0
elif bump == "minor":
    minor, patch = minor + 1, 0
else:
    patch += 1

new = f"{major}.{minor}.{patch}"
version_file.write_text(re.sub(r'"\d+\.\d+\.\d+"', f'"{new}"', text), encoding="utf-8")
print(f"    core/version.py -> {new}")
PY
fi

VERSION="$("$VENV/bin/python" -c 'from core.version import APP_VERSION; print(APP_VERSION)')"
APPIMAGE="FS25-Manager-${VERSION}-x86_64.AppImage"
echo "==> Building FS25 Manager $VERSION"

echo "==> Running tests..."
"$VENV/bin/python" -m unittest discover -p 'test_*.py'

echo "==> Building binary..."
mkdir -p build
if ! "$VENV/bin/pyinstaller" FS25-Manager.spec \
        --distpath dist/linux --workpath build/linux --noconfirm >build/pyinstaller.log 2>&1; then
    cat build/pyinstaller.log
    exit 1
fi

echo "==> Assembling AppDir..."
rm -rf build/AppDir
mkdir -p build/AppDir/usr/bin build/AppDir/usr/share/applications \
         build/AppDir/usr/share/icons/hicolor/scalable/apps
install -m 755 dist/linux/FS25-Manager build/AppDir/usr/bin/FS25-Manager

cat > build/AppDir/AppRun <<'EOF'
#!/bin/sh
HERE="$(dirname "$(readlink -f "$0")")"
exec "$HERE/usr/bin/FS25-Manager" "$@"
EOF
chmod +x build/AppDir/AppRun

cat > build/AppDir/FS25-Manager.desktop <<'EOF'
[Desktop Entry]
Type=Application
Name=FS25 Manager
Exec=FS25-Manager
Icon=fs25-manager
Categories=Utility;
Terminal=false
Comment=FS25 Mod Manager desktop utility
EOF
cp build/AppDir/FS25-Manager.desktop build/AppDir/usr/share/applications/

ICON="ui/icons/agriculture_24dp_E3E3E3_FILL0_wght400_GRAD0_opsz24.svg"
cp "$ICON" build/AppDir/fs25-manager.svg
cp "$ICON" build/AppDir/.DirIcon
cp "$ICON" build/AppDir/usr/share/icons/hicolor/scalable/apps/fs25-manager.svg

TOOL="$HOME/.cache/fs25-manager/appimagetool"
if [ ! -x "$TOOL" ]; then
    echo "==> Fetching appimagetool..."
    mkdir -p "$(dirname "$TOOL")"
    curl -sL -o "$TOOL" \
        https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-x86_64.AppImage
    chmod +x "$TOOL"
fi

echo "==> Packaging AppImage..."
mkdir -p dist
ARCH=x86_64 "$TOOL" build/AppDir "dist/$APPIMAGE" >/dev/null 2>&1

"$VENV/bin/python" - "$VERSION" "$APPIMAGE" <<'PY'
import datetime, json, pathlib, sys

version, appimage = sys.argv[1], sys.argv[2]
manifest_path = pathlib.Path("server-deploy/releases/manifest.json")
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
manifest["version"] = version
manifest["build_date"] = datetime.date.today().isoformat()
manifest["executable"] = appimage
manifest["archive"] = appimage
manifest["download_url"] = (
    f"https://github.com/Loudl3ss/FS25-Mod-Manager/releases/download/v{version}/{appimage}"
)
manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
PY

echo ""
echo "✅ dist/$APPIMAGE  ($(du -h "dist/$APPIMAGE" | cut -f1))"
