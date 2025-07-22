import os
from types import SimpleNamespace
from app.helpers.admin import create_default_roles
from app.schemas.user import UserSchema
from app.tests.user import UserBaseTestCase
from flask_jwt_extended import create_access_token
import pytest

from app.models.user import User
from server import create_app, db


@pytest.fixture(scope='function')
def new_user(test_client):
    user = User(
        email='rhodin@cranecloud.io', password='test_password', name='test_name', organisation='Makerere', username='rhodin')
    user.verified = True
    user.save()
    return user


@pytest.fixture(scope='function')
def test_client():
    flask_app = create_app(config_name='testing')
    # this is for testing purposes - not exact app secret
    flask_app.config['SECRET_KEY'] = "192b9bdd22ab9ed4d12e236c78afcb9a393ec15f71bbf5dc987d54727823bcbf"

    # create a test client using the Flask application configured for testing
    with flask_app.test_client() as testing_client:
        # Establish an application context
        with flask_app.app_context():
            try:
                # Try to create the test database if it doesn't exist
                # First connect to postgres database to create test database
                from sqlalchemy import create_engine
                from sqlalchemy_utils import database_exists, create_database

                # Get the database URI and extract components
                db_uri = flask_app.config['SQLALCHEMY_DATABASE_URI']

                # Create test database if it doesn't exist
                if not database_exists(db_uri):
                    create_database(db_uri)

                # create the database and database tables
                db.engine.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
                db.create_all()
                create_default_roles()

            except Exception as e:
                print(f"Database setup error: {e}")
                # Fallback: try to create tables anyway
                try:
                    db.create_all()
                    create_default_roles()
                except Exception as e2:
                    print(f"Fallback database setup also failed: {e2}")
                    raise

            yield testing_client  # this is where the testing happens
            db.session.remove()
            db.drop_all()


@pytest.fixture(scope='function')
def login_user(test_client):
    user_client = UserBaseTestCase()
    user = user_client.create_user(user_client.user_data)
    token_schema = UserSchema()
    user_dict, errors = token_schema.dump(user)
    access_token = user.generate_token(user_dict)
    return SimpleNamespace(headers={'Authorization': 'Bearer {}'.format(access_token)},
                           user=user)


@pytest.fixture(scope='function')
def admin_login_user(test_client):
    user_client = UserBaseTestCase()
    admin = user_client.create_admin(user_client.admin_data)
    token_schema = UserSchema()
    user_dict, errors = token_schema.dump(admin)
    access_token = admin.generate_token(user_dict)
    return SimpleNamespace(headers={'Authorization': 'Bearer {}'.format(access_token)},
                           admin=admin)
