# Crane Cloud

[![Test](https://github.com/crane-cloud/backend/actions/workflows/test.yml/badge.svg)](https://github.com/crane-cloud/backend/actions/workflows/test.yml)
[![Build](https://github.com/crane-cloud/backend/actions/workflows/staging.yml/badge.svg)](https://github.com/crane-cloud/backend/actions/workflows/staging.yml)
[![codecov](https://codecov.io/gh/crane-cloud/backend/branch/develop/graph/badge.svg?token=kkuF1X6MWx)](https://codecov.io/gh/crane-cloud/backend)

Managed Kubernetes Platform

## Project Setup

Follow these steps to have a local running copy of the app.

### Clone The Repo

```bash
git clone https://github.com/crane-cloud/backend.git
```


### Directly on your machine
---
#### Install PostgreSQL

Here's a great resource to check out: [How To Install and Use PostgreSQL](https://www.digitalocean.com/community/tutorials/how-to-install-and-use-postgresql-on-ubuntu-18-04)

Create the two databases:
- `cranecloud` (for development)
- `cranecloud_test_db` (for unit testing)

#### Create a Virtual Environment

App was developed with Python 3.6.

Make sure you have `pip` installed on your machine.

Create a pip virtual environment called `venv`.

Activate the virtual environment:

```bash
. venv/bin/activate
```

Install the dependencies:

```bash
pip install -r requirements.txt
```

Create a `.env` file (which defines the environment variables used) at the root of the app.

Add the following details, customizing as needed:

```bash
export FLASK_APP=app.py
export FLASK_ENV=development
export FLASK_DEBUG=1
export FLASK_RUN_PORT=5000
export FLASK_APP_SECRET=<app_secret>
```

Run the application:

```bash
flask run
```

### Running application with Docker
---
`make` is a build automation tool that is used to manage the build process of a software project.

- In the project directory, running `make` shows you a list of commands to use.
- Run `make start` to start the application and required services.
- Run `make connect-to-container` to connect to the Flask application container after running `make start`.


---
> Application should be running on http://localhost:5000 and apidocs on http://localhost:5000/apidocs/#/
<!-- --- -->
## Finishing up

>To run with Docker, you have to ssh into the container first by running `make connect-to-container`, and then execute the following commands.

### Running Migrations

The application uses SQLAlchemy ORM to manage and run database migrations.

To run migration upgrade against the database relations, use the following command:

```bash
flask db upgrade
```

To run migrations in case there are changes in the schema, use the following command:

```bash
flask db migrate
```

### Testing and Coverage

This app uses `nose` to run tests.

To run tests with coverage:

```bash
nosetests --with-coverage --cover-package=routes
```

To run tests without coverage:

```bash
nosetests
```

### Creating default roles

To create the default roles, run:

```bash
flask create_roles
```

### Creating default admin account

To create an admin account, run:

```bash
flask admin_user --email=<email> --password=<password> --confirm_password=<password>
```

### To add clusters locally

Run the application using `flask run` and visit [http://127.0.0.1:5000/apidocs/#/clusters/post_clusters](http://127.0.0.1:5000/apidocs/#/clusters/post_clusters)

Use the following JSON payload:

```json
{
  "description": "string",
  "host": "string",
  "name": "string",
  "token": "string"
}
```

Reach out to the backend team to get token and host values.

## Optional things
### Add image repositories

To add image repositories to the database, run:

```bash
flask create_registries
```
### Starting celery workers 
#### Run celery worker and beat on Linux

```bash
celery -A server.celery worker --loglevel=info
celery -A server.celery beat --loglevel=info
```

#### Run celery worker and beat on Windows

```bash
celery -A server.celery worker --pool=solo --loglevel=info
celery -A server.celery beat --loglevel=info
```
