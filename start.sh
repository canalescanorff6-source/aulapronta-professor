#!/usr/bin/env sh
set -e

export FLASK_DEBUG=${FLASK_DEBUG:-0}
export COOKIE_SECURE=${COOKIE_SECURE:-1}
export AULAPRONTA_DB=${AULAPRONTA_DB:-aulapronta.db}
export PORT=${PORT:-5000}

echo "Iniciando AulaPronta Professor..."
echo "PORT=$PORT"
echo "AULAPRONTA_DB=$AULAPRONTA_DB"

gunicorn wsgi:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120
