from app.models.user import User
from app.models import db


def find_user_by_email_or_username(identifier):
    """
    Find a user by either email or username

    Args:
        identifier (str): Email address or username

    Returns:
        User: User object if found, None otherwise
    """
    if not identifier:
        return None

    # First try to find by email
    user = User.find_first(email=identifier)
    if user:
        return user

    # If not found by email, try by username
    user = User.find_first(username=identifier)
    if user:
        return user

    return None


def is_email_or_username(identifier):
    """
    Check if the identifier looks like an email or username

    Args:
        identifier (str): String to check

    Returns:
        str: 'email' if it looks like an email, 'username' otherwise
    """
    if not identifier:
        return 'username'

    # Simple email check - contains @ and has domain structure
    if '@' in identifier and '.' in identifier.split('@')[1]:
        return 'email'

    return 'username'


def validate_login_identifier(identifier):
    """
    Validate login identifier (email or username)

    Args:
        identifier (str): Email or username to validate

    Returns:
        dict: Result with 'valid' (bool), 'type' (str), and 'message' (str)
    """
    result = {
        'valid': False,
        'type': None,
        'message': ''
    }

    if not identifier:
        result['message'] = 'Login identifier is required'
        return result

    if not isinstance(identifier, str):
        result['message'] = 'Login identifier must be a string'
        return result

    identifier = identifier.strip()
    if not identifier:
        result['message'] = 'Login identifier cannot be empty'
        return result

    # Determine if it's email or username
    identifier_type = is_email_or_username(identifier)
    result['type'] = identifier_type

    if identifier_type == 'email':
        # Basic email validation
        if len(identifier) < 5 or len(identifier) > 254:
            result['message'] = 'Email address is too short or too long'
            return result

        # Check for basic email format
        if not '@' in identifier or not '.' in identifier.split('@')[1]:
            result['message'] = 'Invalid email format'
            return result
    else:
        # Username validation
        if len(identifier) < 3 or len(identifier) > 30:
            result['message'] = 'Username must be between 3 and 30 characters'
            return result

        # Check username format
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', identifier):
            result['message'] = 'Username can only contain letters, numbers, underscores, and hyphens'
            return result

    result['valid'] = True
    return result
