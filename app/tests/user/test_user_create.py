import json
from app.tests.user import UserBaseTestCase


# test user creation for success
def test_user_creation_success(test_client):
    """
    GIVEN  right user creation request object
    WHEN the '/users' page is requested (POST)
    THEN check that the response is valid
    """
    user_client = UserBaseTestCase()
    response = test_client.post(
        '/users',
        content_type='application/json',
        data=json.dumps(user_client.user_data),)
    assert response.status_code == 201


def test_user_creation_invalid_info(test_client):
    """
    GIVEN  invalid user creation request object
    WHEN the '/users' page is requested (POST)
    THEN check that the response is valid
    """
    user_client = UserBaseTestCase()
    response = test_client.post(
        '/users',
        content_type='application/json',
        data=json.dumps(user_client.invalid_user_data),)
    assert response.status_code == 400


# test user creation for failure
def test_user_creation_failure(test_client):
    """
    GIVEN  wrong user creation request object
    WHEN the '/users' page is requested (POST)
    THEN check that the response is valid
    """
    user_client = UserBaseTestCase()
    # create a user
    user_client.create_user(user_client.user_data)
    response = test_client.post(
        '/users',
        content_type='application/json',
        data=json.dumps(user_client.user_data),)
    assert response.status_code == 400


# test user creation already exists
def test_user_creation_already_exists(test_client):
    """
    GIVEN  user creation whe user already exists
    WHEN the '/users' page is requested (POST)
    THEN check that the response is valid
    """
    user_client = UserBaseTestCase()
    # create a user
    user_client.create_user(user_client.user_data)
    response = test_client.post(
        '/users',
        content_type='application/json',
        data=json.dumps(user_client.user_data),)
    assert response.status_code == 400


# # Test get user info
# def test_get_user_info(test_client):
#     """
#     GIVEN  user login credentials
#     WHEN the '/users/<user_id>' page is requested (GET)
#     THEN check that the response is valid
#     """
#     user_client = UserBaseTestCase()
#     user = user_client.create_user(user_client.user_data)
#     # access_token = create_access_token(user_client.user_data)
#     # headers={'Authorization': 'Bearer {}'.format(access_token)}

#     response = test_client.get(
#         f'/users/${user.id}', 
#         # headers=headers
#         )
    
#     assert response.status_code == 200
