# Crane Cloud

[![codecov](https://codecov.io/gh/crane-cloud/backend/branch/develop-new/graph/badge.svg?token=kkuF1X6MWx)](https://codecov.io/gh/crane-cloud/backend)

Managed Kubernetes Platform

### Project Setup

Follow these steps to have a local running copy of the app.

##### Clone The Repo

`git clone https://github.com/crane-cloud/backend.git`

If `master` is not up to date, `git checkout develop-new`. However, note that code on develop-new could be having some minor issues to sort.

##### Install PostgreSQL

Here's a great resource to check out:

[How To Install and Use PostgreSQL](https://www.digitalocean.com/community/tutorials/how-to-install-and-use-postgresql-on-ubuntu-18-04)

Create the two databases `cranecloud` (for development) and `cranecloud_test_db` (for unit testing).

##### Create a Virtual Environment

App was developed with `Python 3.6`.

Make sure you have `pip` installed on your machine.

Create a pip virtual environment you can call it `venv`

Activate the virtual environment.

`. venv/bin/activate`

Install the dependencies.

`pip install -r requirements.txt`

Create a `.env` file (which defines the environment variables used) at the root of the app.

Add the following details, customizing as needed.

```
export FLASK_APP=app.py
export FLASK_ENV=development
export FLASK_DEBUG=1
export FLASK_RUN_PORT=5000
export FLASK_APP_SECRET=<app_secret>
```

Run the application.

`flask run`

#### Running Migrations

The application uses sqlalchemy ORM to manange and run database migrations

Run `python manage.py db upgrade` command to run migration upgrade against the database relations

Run `python manage.py db migrate` command to run migrations incase there are changes in the schema

##### Testing and Coverage

This app uses `nose` to run tests.

`nosetests --with-coverage --cover-package=routes` to run with coverage

or `nosetests` to run without coverage

##### Creating default roles

To create the default roles

`python manage.py create_roles`

##### Creating default admin account

To create an admin account run

`python manage.py admin_user --email=<an email> --password=<the password> --confirm_password=<the password>`

#### To add clusters locally

Run the application using `flask run` and visit `http://127.0.0.1:5000/apidocs/#/clusters/post_clusters`

`{ "description": "string", "host": "string", "name": "string", "token": "string" }`
Reach out to backend team to get token and host values

##### Add image repositories

To add image repositories to the database run

`python manage.py create_registries`

##### Run celery worker and beat on linux with

`celery -A server.celery worker --loglevel=info`
`celery -A server.celery beat --loglevel=info`

##### Run celery worker and beat on windows with

`celery -A server.celery worker --pool=solo --loglevel=info`
`celery -A server.celery beat --loglevel=info`
