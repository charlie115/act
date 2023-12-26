#!/bin/bash

echo "Running migrations..."
python manage.py migrate
python manage.py migrate --database=messagecore

echo "Starting server.."
python manage.py runserver 0.0.0.0:8000
