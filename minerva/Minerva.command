#!/usr/bin/env bash
# Double-click to run Minerva from source. Needs Python 3; Excel export and PDF reading use two small optional packages.
cd "$(dirname "$0")"
python3 -c "import openpyxl, pypdf" 2>/dev/null || python3 -m pip install --user --quiet openpyxl pypdf 2>/dev/null || true
python3 run.py --browser
