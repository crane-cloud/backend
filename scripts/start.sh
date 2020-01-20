#! /bin/bash

# source env variables
source .env

#while ! nc -z database 5432; do
#    sleep 0.1
#done
# apply migrations onto db
python manage.py db upgrade

# start server
flask run --host=0.0.0.0 --port=5000