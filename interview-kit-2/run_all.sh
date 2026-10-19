#!/usr/bin/env bash
# Run every reference solution (each has its own asserts), then check the starters.
set -euo pipefail
cd "$(dirname "$0")"
PY="${PYTHON:-python3}"
if [ -d solutions ]; then SOL=solutions; else SOL=.; fi
"$PY" -c "import sys, numpy, pandas; print('python', sys.version.split()[0], '| numpy', numpy.__version__, '| pandas', pandas.__version__)"
for f in "$SOL"/p[0-9]_*.py; do echo "== $(basename "$f")"; "$PY" "$f"; done
echo "== starters"; "$PY" test_starters.py
