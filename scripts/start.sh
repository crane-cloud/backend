#! /bin/bash

# source .env

# apply migrations onto db
flask db upgrade

# start server
flask run --host=0.0.0.0 --port=5000