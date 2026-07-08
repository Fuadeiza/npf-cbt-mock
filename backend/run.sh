#!/usr/bin/env bash
# Set up (once) and run the app. Serves the API + frontend on http://localhost:8000
set -euo pipefail
cd "$(dirname "$0")"

if [ ! -d .venv ]; then
  python3 -m venv .venv
  ./.venv/bin/pip install --quiet -r requirements.txt
fi

exec ./.venv/bin/uvicorn app.main:app --reload --port 8000
