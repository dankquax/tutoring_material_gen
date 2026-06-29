#!/usr/bin/env bash
# Verification script: compiles one .tex file from 05_output/ with pdflatex
# and reports a clear PASS/FAIL. Cleans up all compilation artifacts on success.

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

TINYTEX_BIN="$HOME/AppData/Roaming/TinyTeX/bin/windows"
if [ -d "$TINYTEX_BIN" ]; then
  PATH="$PATH:$TINYTEX_BIN"
fi

if ! command -v pdflatex >/dev/null 2>&1; then
  echo "FAIL: pdflatex not found on PATH. Run ./init.sh to check the toolchain." >&2
  exit 1
fi

echo "==> Verifying LaTeX syntax for $TEX_BASENAME..."
cd "$OUTPUT_DIR"

BASE_NAME="${TEX_BASENAME%.tex}"
LOG_NAME="$BASE_NAME.log"
STDOUT_NAME="$LOG_NAME.stdout"

# Run compilation pass quietly
if pdflatex -interaction=nonstopmode -halt-on-error "$TEX_BASENAME" > "$STDOUT_NAME" 2>&1; then
  echo "PASS: Syntax is perfectly valid."
  echo "==> Cleaning up verification clutter from 05_output/..."
  
  # Automatically vaporize all auxiliary files and the byproduct PDF on success
  rm -f "$BASE_NAME.aux" "$LOG_NAME" "$BASE_NAME.out" "$BASE_NAME.pdf" "$STDOUT_NAME" "$BASE_NAME.toc" "$BASE_NAME.synctex.gz"
  exit 0
else
  echo "FAIL: pdflatex reported errors compiling $TEX_BASENAME." >&2
  echo "      Logs preserved for debugging: $OUTPUT_DIR/$LOG_NAME and $STDOUT_NAME" >&2
  grep -m 5 '^!' "$LOG_NAME" >&2 2>/dev/null || true
  exit 1
fi