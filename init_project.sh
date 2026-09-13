#!/usr/bin/env bash
set -eu

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

VENV_DIR="${VENV_DIR:-venv}"
SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE:-axatel.settings.dev}"

if [ ! -d "$VENV_DIR" ]; then
  echo "[init] Creating virtual environment in $VENV_DIR"
  python3 -m venv "$VENV_DIR"
fi

# shellcheck disable=SC1090
source "$VENV_DIR/bin/activate"

if [ ! -f requirements.txt ]; then
  echo "[init] requirements.txt not found in $ROOT_DIR"
  exit 1
fi

pip install --upgrade pip >/dev/null
pip install -r requirements.txt

if [ ! -f .env ]; then
  if [ -f .env.example ]; then
    echo "[init] Creating .env from .env.example"
    cp .env.example .env
  else
    echo "[init] Missing .env.example; create your environment file manually."
    exit 1
  fi
fi

mkdir -p logs media staticfiles

export DJANGO_SETTINGS_MODULE="$SETTINGS_MODULE"

echo "[init] Running database migrations..."
python manage.py migrate --noinput

echo "[init] Collecting static files..."
python manage.py collectstatic --noinput

echo "[init] Seeding default content..."
python manage.py seed_casi >/dev/null || true
python manage.py seed_chatbot_kb >/dev/null || true

if [ -n "${DJANGO_SUPERUSER_USERNAME:-}" ] || [ -n "${DJANGO_SUPERUSER_EMAIL:-}" ]; then
  echo "[init] Creating superuser if needed..."
  python manage.py createsuperuser --noinput \
    --username "${DJANGO_SUPERUSER_USERNAME:-admin}" \
    --email "${DJANGO_SUPERUSER_EMAIL:-admin@example.com}" \
    || true
fi

echo "[init] Initialization complete."
echo "[init] Start the app with: python manage.py runserver 0.0.0.0:8000"
