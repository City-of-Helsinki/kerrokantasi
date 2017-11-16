#!/bin/sh
echo "Doing migrations (in $HOME)"
cd $HOME/kerrokantasi
../venv/bin/python manage.py migrate
echo "Starting uwsgi"
uwsgi --yml /etc/uwsgi/apps-available/kerrokantasi-api.yml
