#!/usr/bin/env bash
set -eu

# Backend-only VPS bootstrap for Axatel
# - Ubuntu + MariaDB/MySQL
# - Python venv
# - gunicorn + nginx
# - no Docker

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

VENV_DIR="${VENV_DIR:-venv}"
SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE:-axatel.settings.production}"
SKIP_STATIC="${SKIP_STATIC:-1}"

if [ ! -d "$VENV_DIR" ]; then
  echo "[server] Creating virtualenv"
  python3 -m venv "$VENV_DIR"
fi

# shellcheck disable=SC1090
source "$VENV_DIR/bin/activate"

python -m pip install --upgrade pip
pip install -r requirements.txt

if [ ! -f .env ]; then
  if [ -f .env.example ]; then
    echo "[server] Creating .env from .env.example"
    cp .env.example .env
  else
    echo "[server] Missing .env.example. Create .env manually first."
    exit 1
  fi
fi

mkdir -p logs media staticfiles

export DJANGO_SETTINGS_MODULE="$SETTINGS_MODULE"

echo "[server] Running migrations"
python manage.py migrate --noinput

if [ "$SKIP_STATIC" != "1" ]; then
  echo "[server] Collecting static files for Django admin/assets only"
  python manage.py collectstatic --noinput
else
  echo "[server] Skipping static collection: backend-only deploy; media/admin assets are served separately"
fi

echo "[server] Deploy bootstrap complete"
echo "[server] Start the app with: gunicorn axatel.wsgi:application --bind 0.0.0.0:8000"
