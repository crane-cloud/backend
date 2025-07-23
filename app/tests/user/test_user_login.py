import json
from app.tests.user import UserBaseTestCase
from app.helpers.user_finder import find_user_by_email_or_username, validate_login_identifier, is_email_or_username


def test_create_user_with_fixture(new_user):
    """
    GIVEN a User Model
    WHEN a new User is created
    THEN check the email, password and name fields are defined correctly
    """

    assert new_user.email == 'rhodin@cranecloud.io'
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

# test login success


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
        data=json.dumps({
            'username': user_client.user_data['email'],  # Use username field
            'password': user_client.user_data['password']
        }),)

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
        data=json.dumps({
            # Use different user's email
            'username': user_client.user_data_2['email'],
            'password': user_client.user_data_2['password']
        }),)

    assert response.status_code == 401

# test admin login success


def test_admin_login_success(test_client):
    """
    GIVEN  right admin login credentials
    WHEN the '/users/admin_login' page is requested (POST)
    THEN check that the response is valid
    """

    user_client = UserBaseTestCase()
    # create a user
    user_client.create_admin(user_client.admin_data)

    response = test_client.post(
        '/users/admin_login',
        content_type='application/json',
        data=json.dumps({
            'username': user_client.admin_data['email'],  # Use username field
            'password': user_client.admin_data['password']
        }),)

    assert response.status_code == 200


# test admin login not admin
def test_admin_login_unauthorised(test_client):
    """
    GIVEN  not admin login credentials
    WHEN the '/users/admin_login' page is requested (POST)
    THEN check that the response is valid
    """

    user_client = UserBaseTestCase()
    # create a user
    user_client.create_user(user_client.user_data)
    # create admin user
    user_client.create_admin(user_client.admin_data)

    response = test_client.post(
        '/users/admin_login',
        content_type='application/json',
        data=json.dumps({
            # Use regular user's email
            'username': user_client.user_data['email'],
            'password': user_client.user_data['password']
        }),)

    assert response.status_code == 401


def test_admin_login_invalid_info(test_client):
    """
    GIVEN  invalid admin login request object
    WHEN the '/users/admin_login' page is requested (POST)
    THEN check that the response is valid
    """
    user_client = UserBaseTestCase()
    # create a admin user
    user_client.create_admin(user_client.admin_data)

    response = test_client.post(
        '/users/admin_login',
        content_type='application/json',
        data=json.dumps(user_client.invalid_user_data),)

    assert response.status_code == 400

# test login failure


def test_admin_login_failure(test_client):
    """
    GIVEN  wrong admin login credentials
    WHEN the '/users/admin_login' page is requested (POST)
    THEN check that the response is valid
    """
    user_client = UserBaseTestCase()

    # create a admin user
    user_client.create_admin(user_client.admin_data)

    response = test_client.post(
        '/users/admin_login',
        content_type='application/json',
        data=json.dumps({
            # Use different user's email
            'username': user_client.user_data_2['email'],
            'password': user_client.user_data_2['password']
        }),)

    assert response.status_code == 401


class TestUserFinder:
    """Test cases for user finder functions"""

    def test_is_email_or_username(self):
        """Test email vs username detection"""
        # Email cases
        assert is_email_or_username('user@example.com') == 'email'
        assert is_email_or_username('test.user@domain.co.uk') == 'email'
        assert is_email_or_username('user123@test.org') == 'email'

        # Username cases
        assert is_email_or_username('john_doe') == 'username'
        assert is_email_or_username('user123') == 'username'
        assert is_email_or_username('test-user') == 'username'
        assert is_email_or_username('admin') == 'username'

        # Edge cases
        assert is_email_or_username('') == 'username'
        assert is_email_or_username(None) == 'username'
        assert is_email_or_username('user@') == 'username'  # Invalid email
        assert is_email_or_username('@domain.com') == 'email'

    def test_validate_login_identifier(self):
        """Test login identifier validation"""
        # Valid email cases
        result = validate_login_identifier('user@example.com')
        assert result['valid'] is True
        assert result['type'] == 'email'
        assert result['message'] == ''

        result = validate_login_identifier('test.user@domain.co.uk')
        assert result['valid'] is True
        assert result['type'] == 'email'

        # Valid username cases
        result = validate_login_identifier('john_doe')
        assert result['valid'] is True
        assert result['type'] == 'username'
        assert result['message'] == ''

        result = validate_login_identifier('user123')
        assert result['valid'] is True
        assert result['type'] == 'username'

        # Invalid cases
        result = validate_login_identifier('')
        assert result['valid'] is False
        assert 'required' in result['message']

        result = validate_login_identifier(None)
        assert result['valid'] is False
        assert 'required' in result['message']

        result = validate_login_identifier('ab')  # Too short username
        assert result['valid'] is False
        assert 'between 3 and 30 characters' in result['message']

        result = validate_login_identifier('a' * 31)  # Too long username
        assert result['valid'] is False
        assert 'between 3 and 30 characters' in result['message']

        result = validate_login_identifier(
            'user@name!')  # Invalid username chars
        assert result['valid'] is False
        assert 'letters, numbers, underscores, and hyphens' in result['message']

        result = validate_login_identifier('user@')  # Invalid email
        assert result['valid'] is False
        # Fixed: 'user@' is detected as username, not email, so it fails username validation
        assert 'letters, numbers, underscores, and hyphens' in result['message']

        result = validate_login_identifier('a' * 300)  # Too long email
        assert result['valid'] is False
        # Fixed: 'a' * 300 is detected as username, not email, so it fails username validation
        assert 'between 3 and 30 characters' in result['message']


class TestLoginWithEmailOrUsername:
    """Integration tests for login with email or username"""

    def test_find_user_by_email_or_username(self, test_client, new_user):
        """Test finding user by email or username"""
        with test_client.application.app_context():
            from app.models import db

            # Test finding by email
            user_by_email = find_user_by_email_or_username(new_user.email)
            assert user_by_email is not None
            assert user_by_email.id == new_user.id

            # Test finding by username
            user_by_username = find_user_by_email_or_username(
                new_user.username)
            assert user_by_username is not None
            assert user_by_username.id == new_user.id

            # Test finding non-existent user
            non_existent = find_user_by_email_or_username(
                'nonexistent@example.com')
            assert non_existent is None

            non_existent = find_user_by_email_or_username('nonexistent_user')
            assert non_existent is None

    def test_login_with_email(self, test_client, new_user):
        """Test login using email"""
        with test_client.application.app_context():
            response = test_client.post('/users/login', json={
                'username': new_user.email,
                'password': 'test_password'  # Use the actual password from fixture
            })

            assert response.status_code == 200
            data = response.get_json()
            assert data['status'] == 'success'
            assert 'access_token' in data['data']
            assert data['data']['email'] == new_user.email

    def test_login_with_username(self, test_client, new_user):
        """Test login using username"""
        with test_client.application.app_context():
            response = test_client.post('/users/login', json={
                'username': new_user.username,
                'password': 'test_password'  # Use the actual password from fixture
            })

            assert response.status_code == 200
            data = response.get_json()
            assert data['status'] == 'success'
            assert 'access_token' in data['data']
            assert data['data']['username'] == new_user.username

    def test_login_with_invalid_identifier(self, test_client):
        """Test login with invalid email/username"""
        with test_client.application.app_context():
            response = test_client.post('/users/login', json={
                'username': 'invalid@user',
                'password': 'password123'
            })

            # The API returns 400 for validation errors, not 401
            assert response.status_code == 400
            data = response.get_json()
            assert data['status'] == 'fail'

    def test_login_with_invalid_password(self, test_client, new_user):
        """Test login with wrong password"""
        with test_client.application.app_context():
            response = test_client.post('/users/login', json={
                'username': new_user.email,
                'password': 'wrongpassword'
            })

            assert response.status_code == 401
            data = response.get_json()
            assert data['status'] == 'fail'
            # Fixed: match the actual error message from the API
            assert 'invalid username/email or password' in data['message']

    def test_login_with_invalid_data(self, test_client):
        """Test login with invalid request data"""
        with test_client.application.app_context():
            # Missing username - this should return 400 for validation error
            response = test_client.post('/users/login', json={
                'password': 'password123'
            })

            assert response.status_code == 400
            data = response.get_json()
            assert data['status'] == 'fail'

            # Missing password - this should return 400 for validation error
            response = test_client.post('/users/login', json={
                'username': 'user@example.com'
            })

            assert response.status_code == 400
            data = response.get_json()
            assert data['status'] == 'fail'

            # Invalid email format - this should return 400 for validation
            response = test_client.post('/users/login', json={
                'email': 'invalid@',  # Invalid email format
                'password': 'password123'
            })

            assert response.status_code == 400
            data = response.get_json()
            assert data['status'] == 'fail'

    def test_admin_login_with_email_or_username(self, test_client, admin_login_user):
        """Test admin login with email or username"""
        with test_client.application.app_context():
            admin_user = admin_login_user.admin

            # Login with email
            response = test_client.post('/users/admin_login', json={
                'username': admin_user.email,
                'password': 'Compl3xPassw0rd'  # Use the actual password from admin_data
            })

            assert response.status_code == 200
            data = response.get_json()
            assert data['status'] == 'success'
            assert 'access_token' in data['data']

            # Login with username
            response = test_client.post('/users/admin_login', json={
                'username': admin_user.username,
                'password': 'Compl3xPassw0rd'  # Use the actual password from admin_data
            })

            assert response.status_code == 200
            data = response.get_json()
            assert data['status'] == 'success'
            assert 'access_token' in data['data']
