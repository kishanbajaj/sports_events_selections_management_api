#!/bin/sh

#export APP_MODULE=${APP_MODULE-app.main:app}
export APP_MODULE=${APP_MODULE-app.main:app}
export HOST=${HOST:-0.0.0.0}
export PORT=${PORT:-8000}

echo 'Running migrations'
poetry run alembic upgrade head
echo 'Migrations completed'

exec uvicorn --reload --host $HOST --port $PORT "$APP_MODULE"