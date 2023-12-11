#!/bin/bash

echo "Running migrations..."
python manage.py migrate --settings=config.settings.prod

echo "Running collectstatic..."
python manage.py collectstatic --settings=config.settings.prod --noinput

echo "Starting gunicorn server..."
gunicorn config.wsgi --bind 0.0.0.0:8000 --timeout 60 --access-logfile - --error-logfile -
