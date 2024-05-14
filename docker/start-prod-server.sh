#!/bin/bash

echo "Running migrations..."
python manage.py migrate --settings=config.settings.prod
python manage.py migrate --settings=config.settings.prod --database=messagecore

echo "Loading fixtures..."
python manage.py loaddata infocore.marketcode.json
python manage.py loaddata fee.feerate.json

echo "Running collectstatic..."
python manage.py collectstatic --settings=config.settings.prod --noinput

echo "Starting daphne server..."
# gunicorn config.wsgi --bind 0.0.0.0:8000 --timeout 60 --access-logfile - --error-logfile -
daphne -b 0.0.0.0 -p 8000 config.asgi:application
