#!/usr/bin/env bash
set -eu

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

VENV_DIR="${VENV_DIR:-venv}"
SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE:-axatel.settings.production}"
SKIP_SEED="${SKIP_SEED:-0}"
CREATE_SUPERUSER="${CREATE_SUPERUSER:-1}"
SKIP_STATIC="${SKIP_STATIC:-1}"

if [ ! -d "$VENV_DIR" ]; then
  echo "[deploy] Creating virtual environment in $VENV_DIR"
  python3 -m venv "$VENV_DIR"
fi

# shellcheck disable=SC1090
source "$VENV_DIR/bin/activate"

if [ ! -f requirements.txt ]; then
  echo "[deploy] requirements.txt not found in $ROOT_DIR"
  exit 1
fi

pip install --upgrade pip >/dev/null
pip install -r requirements.txt

if [ ! -f .env ]; then
  if [ -f .env.example ]; then
    echo "[deploy] Creating .env from .env.example"
    cp .env.example .env
  else
    echo "[deploy] Missing .env.example; create .env manually before continuing."
    exit 1
  fi
fi

mkdir -p logs media staticfiles

export DJANGO_SETTINGS_MODULE="$SETTINGS_MODULE"

echo "[deploy] Running Django migrations..."
python manage.py migrate --noinput

if [ "$SKIP_STATIC" != "1" ]; then
  echo "[deploy] Collecting static files for Django admin/assets only..."
  python manage.py collectstatic --noinput
else
  echo "[deploy] Skipping static collection: backend-only deployment without frontend assets"
fi

if [ "$SKIP_SEED" != "1" ]; then
  echo "[deploy] Seeding default content..."
  python manage.py seed_casi >/dev/null || true
  python manage.py seed_chatbot_kb >/dev/null || true
fi

if [ "$CREATE_SUPERUSER" = "1" ]; then
  if [ -n "${DJANGO_SUPERUSER_USERNAME:-}" ] || [ -n "${DJANGO_SUPERUSER_EMAIL:-}" ]; then
    echo "[deploy] Creating Django superuser if needed..."
    python manage.py createsuperuser --noinput \
      --username "${DJANGO_SUPERUSER_USERNAME:-admin}" \
      --email "${DJANGO_SUPERUSER_EMAIL:-admin@example.com}" \
      || true
  else
    echo "[deploy] Superuser creation skipped. Set DJANGO_SUPERUSER_USERNAME and DJANGO_SUPERUSER_EMAIL to enable it."
  fi
fi

echo "[deploy] Initial deployment setup complete."
echo "[deploy] Start the app with: gunicorn axatel.wsgi:application --bind 0.0.0.0:8000"
