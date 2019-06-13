# Osprey Cloud
[![CircleCI](https://circleci.com/gh/ckwagaba/osprey-backend/tree/develop.svg?style=svg)](https://circleci.com/gh/ckwagaba/osprey-backend/tree/develop)
[![codecov](https://codecov.io/gh/ckwagaba/osprey-backend/branch/develop/graph/badge.svg)](https://codecov.io/gh/ckwagaba/osprey-backend)
<p>Managed Kubernetes Platform</p>

### Project Setup
<p>Follow these steps to have a local running copy of the app.</p>

##### Clone The Repo

``` git clone https://github.com/ckwagaba/osprey-backend.git ```
<p>
If ` master ` is not up to date, `git checkout develop`. However, note that code on develop could be having some minor issues to sort.
</p>

##### Install PostgreSQL
<p>Here's a great resource to check out.</p>

[How To Install and Use PostgreSQL](https://www.digitalocean.com/community/tutorials/how-to-install-and-use-postgresql-on-ubuntu-18-04)

<p>
Create the two databases `osprey` (for development) and `osprey_test_db` (for unit testing).
</p>

##### Create a Virtual Environment
<p>App was developed with `Python 3.6`</p>
<p>Make sure you have `pip` installed on your machine.</p>
<p>Install the dependencies</p>

``` pip install -r requirements.txt ```

<p>
Create a `.env` file (which defines the environment variables used) at the root of the app.
</p>
<p>Add the following details, customizing as needed.</p>

```
export FLASK_APP=app.py
export FLASK_ENV=development
export FLASK_DEBUG=1
export FLASK_RUN_PORT=5000
export FLASK_APP_SECRET=<app_secret>
export KUBE_HOST=<cluster IP>
export KUBE_TOKEN=<cluster access_token>
```

<p>Activate the virtual environment</p>

``` . venv/bin/activate ```

<p>Run the application</p>

``` flask run ```

##### Testing and Coverage
<p>This app uses `nose` to run tests</p>

``` nosetests --with-coverage --cover-package=routes ```