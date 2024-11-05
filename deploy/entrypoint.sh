#!/bin/bash

set -e

if [[ "$WAIT_FOR_IT_HOSTS" ]]; then
    deploy/wait-for-it.sh $WAIT_FOR_IT_HOSTS --timeout=30
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
    exec uwsgi -ini deploy/uwsgi.ini
fi
