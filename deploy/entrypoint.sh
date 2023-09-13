#!/bin/bash

set -e

TIMESTAMP_FORMAT="+%Y-%m-%d %H:%M:%S"

function _log () {
    echo "$(date "$TIMESTAMP_FORMAT")": "$RUN_ID": "$@"
}

function _log_boxed () {
    _log ---------------------------------
    _log "$@"
    _log ---------------------------------
}

_log_boxed "Kerrokantasi container"

if [[ "$1" = "help" ]]; then
    _log "This is a container image for running Kerrokantasi API server"
    _log ""
    _log "By default a production ready server will be started using uWSGI"
    _log "You will need to provide configuration using environment variables, see"
    _log "config_dev.toml for the available variables. Especially important is the"
    _log "database configuration using DATABASE_URL"
    _log ""
    _log "You will need to mount a volume at /srv/media for storing user uploaded"
    _log "media. Otherwise they will be lost at container shutdown."
    _log ""
    _log "In addition to the production server, there are several task commands:"
    _log "- start_django_development_server: runs Django development server at port 8000"
    _log "- initial_data: runs some initial import tasks to populate the database"
    _log "- migrate: runs Django migrations (manage.py migrate)"
    _log "- test: runs Django tests (pytest)"
    _log "- maintenance_tasks: run periodic maintenance tasks, with level as parameter"
    _log "- <anything else>: run command in shell, verbatim"
    _log ""
    _log_boxed "This container will now exit, for your convenience"

    exit 0
fi

_log "Start with \`help\` for instructions"

if [[ "$1" = "start_django_development_server" ]]; then
    _log_boxed "Running development server"
    exec deploy/dev_start.sh
elif [[ "$1" = "maintenance_tasks" ]]; then
    _log_boxed "Running scheduled data imports and maintenance"
    deploy/run_maintenance.sh
elif [[ "$1" = "initial_data" ]]; then
    _log_boxed "Running initial imports to get test data"
    deploy/run_maintenance.sh
elif [[ "$1" = "migrate" ]]; then
    _log_boxed "Running migrations"
    ./manage.py migrate
    _log_boxed "Updating language fields & installing templates"
    deploy/init_application.sh
elif [[ "$1" = "test" ]]; then
    _log_boxed "Running flake8"
    flake8 democracy
#     _log_boxed "Running black"
#     black --check .
#     _log_boxed "Running isort"
#     isort --check-only --diff .
    _log_boxed "Running safety"
    safety check -r requirements.txt
    _log_boxed "Running tests"
    pytest
elif [[ -n "$*" ]]; then
    _log_boxed "exec'n $*"
    exec "$@"
else
    _log_boxed "Starting production server"
    exec uwsgi -y deploy/uwsgi.yml
fi

_log_boxed "Hauki entrypoint finished"
