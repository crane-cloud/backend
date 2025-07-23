import pytest
from app.helpers.email_validator import (
    is_valid_username,
    sanitize_username,
    generate_unique_username,
    validate_and_generate_username,
    check_username_availability,
    update_user_username
)


class TestUsernameValidator:
    """Test cases for username validation functions"""

    def test_is_valid_username_valid_cases(self):
        """Test valid username formats"""
        valid_usernames = [
            'john_doe',
            'user123',
            'test-user',
            'admin',
            'user_name_123',
            'a' * 30,  # Maximum length
            'abc'  # Minimum length
        ]

        for username in valid_usernames:
            assert is_valid_username(
                username) is True, f"Username '{username}' should be valid"

    def test_is_valid_username_invalid_cases(self):
        """Test invalid username formats"""
        invalid_usernames = [
            '',  # Empty string
            None,  # None value
            'ab',  # Too short
            'a' * 31,  # Too long
            'user@name',  # Invalid character
            'user name',  # Space
            'user.name',  # Dot
            'user/name',  # Slash
            'user\\name',  # Backslash
            'user:name',  # Colon
            'user;name',  # Semicolon
            'user,name',  # Comma
            'user!name',  # Exclamation
            'user?name',  # Question mark
            'user#name',  # Hash
            'user$name',  # Dollar
            'user%name',  # Percent
            'user^name',  # Caret
            'user&name',  # Ampersand
            'user*name',  # Asterisk
            'user(name',  # Parenthesis
            'user)name',  # Parenthesis
            'user+name',  # Plus
            'user=name',  # Equals
            'user[name',  # Bracket
            'user]name',  # Bracket
            'user{name',  # Brace
            'user}name',  # Brace
            'user|name',  # Pipe
            'user~name',  # Tilde
            'user`name',  # Backtick
            'user<name',  # Less than
            'user>name',  # Greater than
            'user"name',  # Quote
            "user'name",  # Single quote
        ]

        for username in invalid_usernames:
            assert is_valid_username(
                username) is False, f"Username '{username}' should be invalid"

    def test_sanitize_username(self):
        """Test username sanitization"""
        test_cases = [
            ('John Doe', 'john_doe'),
            ('user@name.com', 'user_name_com'),
            # Fixed: exclamation gets converted to underscore, then stripped
            ('user name!', 'user_name'),
            # Fixed: hyphens are valid characters, so they stay
            ('USER-NAME', 'user-name'),
            ('user___name', 'user_name'),
            ('_user_name_', 'user_name'),
            ('user123', 'user123'),
            ('a' * 35, 'a' * 30),  # Truncate long usernames
            ('ab', None),  # Too short after sanitization
            ('', None),  # Empty
            (None, None),  # None
        ]

        for input_username, expected in test_cases:
            result = sanitize_username(input_username)
            assert result == expected, f"Expected '{expected}' for input '{input_username}', got '{result}'"

    def test_validate_and_generate_username_with_provided_username(self):
        """Test validation with provided username"""
        # Valid username
        result = validate_and_generate_username(username='testuser')
        assert result['success'] is True
        assert result['username'] == 'testuser'
        assert result['message'] == ''

        # Invalid username
        result = validate_and_generate_username(username='test@user')
        assert result['success'] is False
        assert result['username'] is None
        assert 'Invalid username format' in result['message']

        # Too short username
        result = validate_and_generate_username(username='ab')
        assert result['success'] is False
        assert result['username'] is None
        assert 'Invalid username format' in result['message']

    def test_validate_and_generate_username_from_name(self):
        """Test username generation from name"""
        result = validate_and_generate_username(name='John Doe')
        assert result['success'] is True
        assert result['username'] is not None
        assert len(result['username']) >= 3
        assert len(result['username']) <= 30
        assert result['message'] == ''

    def test_validate_and_generate_username_with_user_id(self):
        """Test username validation for existing user updates"""
        # This would need a database test setup
        # For now, just test the function signature
        result = validate_and_generate_username(
            username='testuser',
            user_id='some-user-id'
        )
        assert 'success' in result
        assert 'username' in result
        assert 'message' in result

    def test_check_username_availability(self):
        """Test username availability checking"""
        # This would need a database test setup
        # For now, just test the function signature
        result = check_username_availability('testuser')
        assert 'available' in result
        assert 'message' in result
        assert isinstance(result['available'], bool)

    def test_generate_unique_username(self):
        """Test unique username generation"""
        # This would need a database test setup
        # For now, just test the function signature
        result = generate_unique_username('John Doe')
        # Should return a string or None
        assert result is None or isinstance(result, str)
        if result:
            assert len(result) >= 3
            assert len(result) <= 30
            assert is_valid_username(result)


class TestUsernameValidatorIntegration:
    """Integration tests for username validation with database"""

    def test_username_uniqueness_check(self, test_client):
        """Test that username uniqueness is properly checked"""
        with test_client.application.app_context():
            from app.models import db

            # Check that new username is available
            result = check_username_availability(
                'newuser', db_session=db.session)
            assert result['available'] is True
            assert 'available' in result['message']

    def test_username_generation_with_existing_user(self, test_client):
        """Test username generation when similar usernames exist"""
        with test_client.application.app_context():
            from app.models import db

            # Generate username from name
            result = validate_and_generate_username(
                name='Test User', db_session=db.session)
            assert result['success'] is True
            assert is_valid_username(result['username'])

    def test_update_user_username(self, test_client, new_user):
        """Test updating user username"""
        with test_client.application.app_context():
            from app.models import db

            # Update with valid username
            result = update_user_username(
                new_user, 'newusername', db_session=db.session)
            assert result['success'] is True
            assert result['username'] == 'newusername'

            # Verify in database
            from app.models.user import User
            updated_user = User.find_first(email=new_user.email)
            assert updated_user.username == 'newusername'

            # Try to update with invalid username
            result = update_user_username(
                new_user, 'invalid@username', db_session=db.session)
            assert result['success'] is False
            assert 'Invalid username format' in result['message']
