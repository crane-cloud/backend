
# Crane Cloud

[![CircleCI](https://circleci.com/gh/crane-cloud/backend/tree/develop.svg?style=svg)](https://circleci.com/gh/crane-cloud/backend/tree/develop)
[![codecov](https://codecov.io/gh/crane-cloud/backend/branch/develop/graph/badge.svg)](https://codecov.io/gh/crane-cloud/backend)

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

Activate the virtual environment.

`. venv/bin/activate`

Run the application.

`flask run`

##### Testing and Coverage

This app uses `nose` to run tests.

`nosetests --with-coverage --cover-package=routes`

##### Creating default roles

To create the default roles

`python manage.py create_roles`


##### Creating default admin account

To create an admin account run

`python manage.py admin_user --email=<an email> --password=<the password> --confirm_password=<the password>`

##### Add image repositories

To add image repositories to the database run

`python manage.py create_registries`

