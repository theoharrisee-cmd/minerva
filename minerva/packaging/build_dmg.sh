#!/usr/bin/env bash
# Build Minerva.dmg on macOS. Usage:  ./packaging/build_dmg.sh
# Produces dist/Minerva.dmg for the architecture of the Mac you run it on.
set -euo pipefail
cd "$(dirname "$0")/.."

PY="${PYTHON:-python3}"
"$PY" -m venv .buildenv
source .buildenv/bin/activate
python -m pip install --quiet --upgrade pip
python -m pip install --quiet pywebview pyinstaller pypdf openpyxl

python run.py --selftest            # fail fast if the source tree is broken

rm -rf build dist
pyinstaller --noconfirm --clean --windowed --name Minerva \
  --icon packaging/Minerva.icns \
  --osx-bundle-identifier com.minerva.app \
  --add-data "ui:ui" --add-data "core/snapshot.json:core" --add-data "core/demo_docs:core/demo_docs" \
  --hidden-import openpyxl --hidden-import pypdf \
  --collect-submodules webview \
  run.py

# Ad-hoc sign so Apple Silicon will launch it (no Developer ID needed)
codesign --force --deep --sign - dist/Minerva.app

# Prove the packaged app boots (headless self-test)
dist/Minerva.app/Contents/MacOS/Minerva --selftest

STAGE="$(mktemp -d)"
cp -R dist/Minerva.app "$STAGE/"
ln -s /Applications "$STAGE/Applications"
hdiutil create -volname "Minerva" -srcfolder "$STAGE" -ov -format UDZO "dist/Minerva.dmg"
rm -rf "$STAGE"

echo
echo "Built dist/Minerva.dmg"
echo "First launch: right-click Minerva.app, choose Open (the app is not notarised)."
