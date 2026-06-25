#!/usr/bin/env bash
# Verification script: compiles one .tex file from 05_output/ with pdflatex
# and reports a clear PASS/FAIL. Usage:
#   ./compile.sh Topic_01_Data_Representation.tex
#   ./compile.sh 05_output/Topic_01_Data_Representation.tex

set -uo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUTPUT_DIR="$ROOT_DIR/05_output"

if [ "$#" -ne 1 ]; then
  echo "Usage: $0 <file>.tex" >&2
  exit 2
fi

TEX_BASENAME="$(basename "$1")"
TEX_PATH="$OUTPUT_DIR/$TEX_BASENAME"

if [ ! -f "$TEX_PATH" ]; then
  echo "FAIL: $TEX_PATH does not exist." >&2
  exit 1
fi

# Fresh TinyTeX installs land here on Windows; fall back to it if a
# shell restart hasn't picked up the PATH update yet (see init.sh).
TINYTEX_BIN="$HOME/AppData/Roaming/TinyTeX/bin/windows"
if [ -d "$TINYTEX_BIN" ]; then
  PATH="$PATH:$TINYTEX_BIN"
fi

if ! command -v pdflatex >/dev/null 2>&1; then
  echo "FAIL: pdflatex not found on PATH. Run ./init.sh to check the toolchain." >&2
  exit 1
fi

echo "==> Compiling $TEX_BASENAME inside $OUTPUT_DIR"
cd "$OUTPUT_DIR"

LOG_NAME="${TEX_BASENAME%.tex}.log"

if pdflatex -interaction=nonstopmode -halt-on-error "$TEX_BASENAME" > "$LOG_NAME.stdout" 2>&1; then
  echo "PASS: ${TEX_BASENAME%.tex}.pdf compiled with zero errors."
  echo "      Log: $OUTPUT_DIR/$LOG_NAME"
  exit 0
else
  echo "FAIL: pdflatex reported errors compiling $TEX_BASENAME." >&2
  echo "      See $OUTPUT_DIR/$LOG_NAME and $OUTPUT_DIR/$LOG_NAME.stdout for details." >&2
  grep -m 5 '^!' "$LOG_NAME" >&2 2>/dev/null || true
  exit 1
fi
