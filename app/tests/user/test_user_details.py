from app.tests.user import UserBaseTestCase
from flask_jwt_extended import create_access_token


# # Test get user info
def test_get_user_info(test_client, login_user):
    """
    GIVEN  user login credentials
    WHEN the '/users/<user_id>' page is requested (GET)
    THEN check that the response is valid
    """
    response = test_client.get(
        f'/users/{login_user.user.id}', 
        headers=login_user.headers
        )
    assert response.status_code == 200


# Test get user info
def test_get_all_users_admin(test_client, admin_login_user):
    """
    WHEN the '/users' page is requested (GET)
    THEN check that the response is valid for admin
    """

    response = test_client.get(
        f'/users', 
        headers=admin_login_user.headers
        )
        
    assert response.status_code == 200