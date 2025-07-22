import pytest
from app.helpers.user_finder import find_user_by_email_or_username, validate_login_identifier, is_email_or_username


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
        assert is_email_or_username(
            '@domain.com') == 'username'  # Invalid email

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
        assert 'Invalid email format' in result['message']

        result = validate_login_identifier('a' * 300)  # Too long email
        assert result['valid'] is False
        assert 'too short or too long' in result['message']


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
            response = test_client.post('/api/v1/users/login', json={
                'username': new_user.email,
                'password': 'password123'
            })

            assert response.status_code == 200
            data = response.get_json()
            assert data['status'] == 'success'
            assert 'access_token' in data['data']
            assert data['data']['email'] == new_user.email

    def test_login_with_username(self, test_client, new_user):
        """Test login using username"""
        with test_client.application.app_context():
            response = test_client.post('/api/v1/users/login', json={
                'username': new_user.username,
                'password': 'password123'
            })

            assert response.status_code == 200
            data = response.get_json()
            assert data['status'] == 'success'
            assert 'access_token' in data['data']
            assert data['data']['username'] == new_user.username

    def test_login_with_invalid_identifier(self, test_client):
        """Test login with invalid email/username"""
        with test_client.application.app_context():
            response = test_client.post('/api/v1/users/login', json={
                'username': 'invalid@user',
                'password': 'password123'
            })

            assert response.status_code == 401
            data = response.get_json()
            assert data['status'] == 'fail'
            assert 'invalid email/username or password' in data['message']

    def test_login_with_invalid_password(self, test_client, new_user):
        """Test login with wrong password"""
        with test_client.application.app_context():
            response = test_client.post('/api/v1/users/login', json={
                'username': new_user.email,
                'password': 'wrongpassword'
            })

            assert response.status_code == 401
            data = response.get_json()
            assert data['status'] == 'fail'
            assert 'invalid email/username or password' in data['message']

    def test_login_with_invalid_data(self, test_client):
        """Test login with invalid request data"""
        with test_client.application.app_context():
            # Missing username
            response = test_client.post('/api/v1/users/login', json={
                'password': 'password123'
            })

            assert response.status_code == 400
            data = response.get_json()
            assert data['status'] == 'fail'

            # Missing password
            response = test_client.post('/api/v1/users/login', json={
                'username': 'user@example.com'
            })

            assert response.status_code == 400
            data = response.get_json()
            assert data['status'] == 'fail'

            # Invalid email format
            response = test_client.post('/api/v1/users/login', json={
                'username': 'invalid-email',
                'password': 'password123'
            })

            assert response.status_code == 400
            data = response.get_json()
            assert data['status'] == 'fail'

    def test_admin_login_with_email_or_username(self, test_client, admin_user):
        """Test admin login with email or username"""
        with test_client.application.app_context():
            # Login with email
            response = test_client.post('/api/v1/users/admin/login', json={
                'username': admin_user.email,
                'password': 'password123'
            })

            assert response.status_code == 200
            data = response.get_json()
            assert data['status'] == 'success'
            assert 'access_token' in data['data']

            # Login with username
            response = test_client.post('/api/v1/users/admin/login', json={
                'username': admin_user.username,
                'password': 'password123'
            })

            assert response.status_code == 200
            data = response.get_json()
            assert data['status'] == 'success'
            assert 'access_token' in data['data']
