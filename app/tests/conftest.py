import pytest

from app.models.user import User
from app.models import db
from server import create_app


@pytest.fixture(scope='module')
def new_user():
    user = User(
        email='test_email@testdomain.com', password='test_password', name='test_name')
    return user


@pytest.fixture(scope='module')
def test_client():
    flask_app = create_app('flag_test.cfg')

    # create a test client using the Flask application configured for testing
    with flask_app.test_client() as testing_client:
        # Establish an application context
        with flask_app.app_context():
            yield testing_client  # this is where the testing happens
