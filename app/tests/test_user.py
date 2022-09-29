def test_create_user_with_fixture(new_user):
    """
    GIVEN a User Model
    WHEN a new User is created
    THEN check the email, password and name fields are defined correctly
    """

    assert new_user.email == 'test_email@testdomain.com'
    assert new_user.password != 'test_password'
    assert new_user.name == 'test_name'
    assert not new_user.verified
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
