import pytest

from app.models.user import User
from server import create_app, db


@pytest.fixture(scope='module')
def new_user():
    user = User(
        email='test_email@testdomain.com', password='test_password', name='test_name')
    return user


@pytest.fixture(scope='module')
def test_client():
    flask_app = create_app(config_name='testing')

    # create a test client using the Flask application configured for testing
    with flask_app.test_client() as testing_client:
        # Establish an application context
        with flask_app.app_context():
            yield testing_client  # this is where the testing happens


@pytest.fixture(scope='module')
def init_database(test_client):
    # create the database and database tables
    db.create_all()

    # Insert user data
    user_1 = User(
        email='test_email@testdomain.com',
        password='test_password', name='test_name')
    user_2 = User(
        email='test_email_2@testdomain.com',
        password='test_password_2', name='test_name_2')
    db.session.add(user_1)
    db.session.add(user_2)

    # commit the changes for the users
    db.session.commit()

    yield db  # this is where the testing happens

    db.drop_all()


@pytest.fixture(scope='function')
def login_default_user(test_client):
    test_client.post('/users/login',
                     data=dict(email='test_email@testdomain.com', password='test_password'),
                     follow_redirects=True)

    yield  # testing happens
