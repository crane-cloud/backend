import email
import json

from app.tests.user import UserBaseTestCase


def test_create_user_with_fixture(new_user):
    """
    GIVEN a User Model
    WHEN a new User is created
    THEN check the email, password and name fields are defined correctly
    """

    assert new_user.email == 'test_email@testdomain.com'
    assert new_user.password != 'test_password'
    assert new_user.name == 'test_name'
    assert new_user.verified
    assert not new_user.is_beta_user


def test_index_page_with_fixture(test_client):
    """
    GIVEN  a Flask application configured for testing
    WHEN the '/' page is requested (GET)
    THEN check that the response is valid
    """
    response = test_client.get('/')
    assert response.status_code == 200
    assert b"Welcome to Crane Cloud API" in response.data


def test_index_page_post_with_fixture(test_client):
    """
    GIVEN  a Flask application configured for testing
    WHEN the '/' page is requested (GET)
    THEN check that the response is valid
    """
    response = test_client.post('/')
    assert response.status_code == 405
    assert b"Welcome to Crane Cloud API" not in response.data

# test login success, failure and logout
def test_user_login_success(test_client):
    """
    GIVEN  right login credentials
    WHEN the '/users/login' page is requested (POST)
    THEN check that the response is valid
    """
    
    user_client = UserBaseTestCase()
    # create a user
    user_client.create_user(user_client.user_data)
    
    response = test_client.post(
        '/users/login',
        content_type='application/json',
        data=json.dumps(user_client.user_data),)
    
    assert response.status_code == 200

def test_user_login_invalid_info(test_client):
    """
    GIVEN  invalid login request object
    WHEN the '/users/login' page is requested (POST)
    THEN check that the response is valid
    """
    user_client = UserBaseTestCase()
    # create a user
    user_client.create_user(user_client.user_data)
    
    response = test_client.post(
        '/users/login',
        content_type='application/json',
        data=json.dumps(user_client.invalid_user_data),)

    assert response.status_code == 400

# test login failure
def test_user_login_failure(test_client):
    """
    GIVEN  wrong login credentials
    WHEN the '/users/login' page is requested (POST)
    THEN check that the response is valid
    """
    user_client = UserBaseTestCase()
    # create a user
    user_client.create_user(user_client.user_data)
    
    response = test_client.post(
        '/users/login',
        content_type='application/json',
        data=json.dumps(user_client.user_data_2),)

    assert response.status_code == 401