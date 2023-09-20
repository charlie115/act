#!/bin/bash

echo "Running migrations..."
python manage.py migrate

echo "Running collectstatic..."
python manage.py collectstatic --noinput

echo "Starting gunicorn server..."
gunicorn config.wsgi --bind 0.0.0.0:8000 --timeout 60 --access-logfile - --error-logfile -
