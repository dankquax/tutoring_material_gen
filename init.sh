#!/usr/bin/env bash
# Startup script: reports working directory, checks the LaTeX/Python
# toolchain, and ensures the 5 pipeline directories exist. Missing tools are
# reported but do not block directory setup -- this script is meant to be
# safe to run on a fresh checkout before the toolchain is installed.

set -uo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

echo "==> Working directory: $PWD"

status=0

check_cmd() {
  local name="$1"
  shift
  for cmd in "$@"; do
    if command -v "$cmd" >/dev/null 2>&1; then
      echo "==> $name found: $(command -v "$cmd")"
      return 0
    fi
  done
  echo "WARNING: $name not found on PATH (tried: $*). Install it before running feature work that needs it." >&2
  status=1
  return 1
}

check_cmd "pdflatex" pdflatex
check_cmd "python3" python3 python

echo "==> Ensuring core pipeline directories exist"
for d in 00_syllabus 01_raw_sources 02_parsers 03_knowledge_base 04_templates 05_output; do
  mkdir -p "$d"
  echo "    $d/"
done

if [ "$status" -ne 0 ]; then
  echo "==> init.sh finished with warnings (missing toolchain components above)."
else
  echo "==> init.sh finished cleanly."
fi

exit 0
