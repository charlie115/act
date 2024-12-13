#!/bin/bash

echo "Running migrations..."
python manage.py migrate --settings=config.settings.test
python manage.py migrate --settings=config.settings.test --database=messagecore

echo "Loading fixtures..."
python manage.py loaddata users.userrole.json
python manage.py loaddata infocore.marketcode.json
python manage.py loaddata fee.feerate.json
python manage.py loaddata board.level.json
python manage.py loaddata referral.affiliatetier.json
python manage.py loaddata coupon.coupon.json

echo "Starting server.."
python manage.py runserver --settings=config.settings.test 0.0.0.0:8000
