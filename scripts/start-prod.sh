#! /bin/bash


# apply migrations onto db
flask db upgrade

# start server
NEW_RELIC_CONFIG_FILE=newrelic.ini newrelic-admin run-program gunicorn --worker-tmp-dir /dev/shm --workers=4 --bind 0.0.0.0:5000 --timeout 240 server:app

