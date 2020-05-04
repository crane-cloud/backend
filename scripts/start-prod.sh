#! /bin/bash


# apply migrations onto db
python manage.py db upgrade

# start server
gunicorn --worker-tmp-dir /dev/shm --workers=4 --bind 0.0.0.0:5000 --timeout 240 server:app

