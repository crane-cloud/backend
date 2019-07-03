# Osprey Cloud
[![CircleCI](https://circleci.com/gh/osprey-cloud/backend/tree/develop.svg?style=svg)](https://circleci.com/gh/osprey-cloud/backend/tree/develop)
[![codecov](https://codecov.io/gh/ckwagaba/osprey-backend/branch/develop/graph/badge.svg)](https://codecov.io/gh/ckwagaba/osprey-backend)

Managed Kubernetes Platform

### Project Setup
Follow these steps to have a local running copy of the app.

##### Clone The Repo

` git clone https://github.com/ckwagaba/osprey-backend.git `

If `master` is not up to date, `git checkout develop`. However, note that code on develop could be having some minor issues to sort.

##### Install PostgreSQL
Here's a great resource to check out:

[How To Install and Use PostgreSQL](https://www.digitalocean.com/community/tutorials/how-to-install-and-use-postgresql-on-ubuntu-18-04)

Create the two databases `osprey` (for development) and `osprey_test_db` (for unit testing).

##### Create a Virtual Environment
App was developed with `Python 3.6`.

Make sure you have `pip` installed on your machine.

Install the dependencies.

` pip install -r requirements.txt `

Create a `.env` file (which defines the environment variables used) at the root of the app.

Add the following details, customizing as needed.

```
export FLASK_APP=app.py
export FLASK_ENV=development
export FLASK_DEBUG=1
export FLASK_RUN_PORT=5000
export FLASK_APP_SECRET=<app_secret>
export KUBE_HOST=<cluster IP>
export KUBE_TOKEN=<cluster access_token>
```

Activate the virtual environment.

` . venv/bin/activate `

Run the application.

` flask run `

##### Testing and Coverage
This app uses `nose` to run tests.

` nosetests --with-coverage --cover-package=routes `