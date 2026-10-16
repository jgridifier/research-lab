#!/usr/bin/env bash
# Run every reference solution (each has its own asserts), then check the starters.
set -euo pipefail
cd "$(dirname "$0")"
for f in solutions/p*_*.py; do echo "== $f"; python3 "$f"; done
echo "== starters"; python3 test_starters.py
