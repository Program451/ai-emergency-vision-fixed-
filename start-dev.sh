#!/usr/bin/env bash
# Запускает backend (FastAPI, :8000) и frontend (Vite, :5173) параллельно.
# Использование: ./start-dev.sh
# Остановка: Ctrl+C (останавливает оба процесса).

set -e

cleanup() {
  echo ""
  echo "Останавливаю сервисы..."
  kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
  exit 0
}
trap cleanup SIGINT SIGTERM

echo "Запускаю backend на :8000 ..."
(cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload) &
BACKEND_PID=$!

sleep 2

echo "Запускаю frontend на :5173 ..."
(cd frontend && npm run dev) &
FRONTEND_PID=$!

echo ""
echo "Готово:"
echo "  Backend:  http://localhost:8000  (docs: http://localhost:8000/docs)"
echo "  Frontend: http://localhost:5173"
echo ""
echo "Ctrl+C для остановки обоих."

wait $BACKEND_PID $FRONTEND_PID
