#! /bin/bash
source .env
# apply migrations onto db
python manage.py db upgrade

# start server
gunicorn --workers=2 --bind 0.0.0.0:5000 server:app
