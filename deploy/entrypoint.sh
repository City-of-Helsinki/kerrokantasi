#!/bin/bash

set -e

# Wait for database present as docker compose is bringing it up in paraller
if [[ "$WAIT_FOR_IT_ADDRESS" ]]; then
    until nc --verbose --wait 30 -z "$WAIT_FOR_IT_ADDRESS" 5432
    do
      echo "Waiting for postgres database connection..."
      sleep 1
    done
    echo "Database is up!"
fi


if [[ "$APPLY_MIGRATIONS" = "true" ]]; then
    echo "Applying database migrations..."
    ./manage.py migrate --noinput
fi

if [[ "$COMPILE_TRANSLATIONS" = "true" ]]; then
    echo "Compiling translations..."
    django-admin compilemessages
fi

# Allow running arbitrary commands instead of the servers
if [[ -n "$*" ]]; then
    "$@"
elif [[ "$DEV_SERVER" = "true" ]]; then
    echo "Starting development server"
    exec python -Wd ./manage.py runserver 0.0.0.0:8000
else
    echo "Starting production server"
    exec uwsgi --ini deploy/uwsgi.ini
fi
