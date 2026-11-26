#!/bin/sh
# Start Mukoti. Usage: ./run.sh [port]
cd "$(dirname "$0")" || exit 1
PORT="${1:-8000}"
if [ ! -f .env ]; then
  echo "No .env file. Create one with: echo 'CAIMEX_API_KEY=sk-or-...' > .env" >&2
  exit 1
fi
echo "Mukoti is starting. Give it a minute before a demo."
echo "  Patient        http://127.0.0.1:$PORT"
echo "  Nurse's queue  http://127.0.0.1:$PORT/nurse"
echo "  Vitals         http://127.0.0.1:$PORT/vitals"
echo "  Doctor         http://127.0.0.1:$PORT/doctor"
echo "  Pharmacy       http://127.0.0.1:$PORT/pharmacy"
echo "  Waiting room   http://127.0.0.1:$PORT/board"
echo "  Forecast       http://127.0.0.1:$PORT/outbreaks"
echo "  Zimbabwe       http://127.0.0.1:$PORT/national"
echo "  Engine         http://127.0.0.1:$PORT/engine"
echo "  Voice check    http://127.0.0.1:$PORT/check"
exec uv run uvicorn app.server:app --port "$PORT" --log-level warning
