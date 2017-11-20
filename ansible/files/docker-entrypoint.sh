#!/bin/sh
# We want to exit if any step fails
set -e
echo "Doing migrations (in $HOME)"
cd $HOME/kerrokantasi
../venv/bin/python manage.py migrate
echo "Starting uwsgi"
uwsgi --yml /etc/uwsgi/apps-available/kerrokantasi-api.yml
