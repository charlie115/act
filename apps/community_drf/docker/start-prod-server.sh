#!/bin/bash
set -euo pipefail

echo "Running migrations..."
python manage.py migrate --settings=config.settings.prod
python manage.py migrate --settings=config.settings.prod --database=messagecore

echo "Loading fixtures..."
python manage.py loaddata users.userrole.json
python manage.py loaddata infocore.marketcode.json
python manage.py loaddata fee.feerate.json
python manage.py loaddata board.level.json
python manage.py loaddata referral.affiliatetier.json
python manage.py loaddata coupon.coupon.json

echo "Running collectstatic..."
python manage.py collectstatic --settings=config.settings.prod --noinput

echo "Running Django checks..."
python manage.py check --settings=config.settings.prod

echo "Starting daphne server..."
# gunicorn config.wsgi --bind 0.0.0.0:8000 --timeout 60 --access-logfile - --error-logfile -
daphne -b 0.0.0.0 -p 8000 config.asgi:application
