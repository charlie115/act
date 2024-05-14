#!/bin/bash

echo "Running migrations..."
python manage.py migrate
python manage.py migrate --database=messagecore

echo "Loading fixtures..."
python manage.py loaddata infocore.marketcode.json
python manage.py loaddata fee.feerate.json

echo "Starting server.."
python manage.py runserver 0.0.0.0:8000
