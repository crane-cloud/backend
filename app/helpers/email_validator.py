import re
import random
import string
from datetime import datetime


def is_valid_email(email):
    """Check if email is valid"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def is_valid_username(username):
    """
    Check if username is valid - single string with allowed characters

    Args:
        username (str): Username to validate

    Returns:
        bool: True if username is valid, False otherwise
    """
    if not username or not isinstance(username, str):
        return False

    # Check length
    if len(username) < 3 or len(username) > 30:
        return False

    # Check pattern - only letters, numbers, underscores, and hyphens
    pattern = r'^[a-zA-Z0-9_-]+$'
    return re.match(pattern, username) is not None


def sanitize_username(username):
    """
    Sanitize username to ensure it's a valid single string

    Args:
        username (str): Raw username input

    Returns:
        str: Sanitized username or None if invalid
    """
    if not username or not isinstance(username, str):
        return None

    # Remove any whitespace and convert to lowercase
    sanitized = username.strip().lower()

    # Replace invalid characters with underscores
    sanitized = re.sub(r'[^a-z0-9_-]', '_', sanitized)

    # Remove consecutive underscores
    sanitized = re.sub(r'_+', '_', sanitized)

    # Remove leading/trailing underscores
    sanitized = sanitized.strip('_')

    # Ensure minimum length
    if len(sanitized) < 3:
        return None

    # Truncate if too long
    if len(sanitized) > 30:
        sanitized = sanitized[:30]

    return sanitized


def generate_unique_username(base_name, max_attempts=10, db_session=None):
    """
    Generate a unique username from a base name

    Args:
        base_name (str): Base name to generate username from
        max_attempts (int): Maximum attempts to find unique username
        db_session: Database session for checking uniqueness

    Returns:
        str: Unique username or None if failed
    """
    if not base_name:
        return None

    # Sanitize the base name
    base_username = sanitize_username(base_name)
    if not base_username:
        base_username = 'user'

    # If no db session provided, return base username
    if not db_session:
        return base_username

    # Try to use base username first
    from app.models.user import User
    if not db_session.query(User).filter_by(username=base_username).first():
        return base_username

    # Try with random suffixes
    for attempt in range(1, max_attempts + 1):
        if attempt <= 5:
            # Use random 3-digit suffix
            suffix = ''.join(random.choices(string.digits, k=3))
            test_username = f"{base_username}{suffix}"
        else:
            # Use timestamp as fallback
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            test_username = f"{base_username}{timestamp}"

        # Check if username exists
        if not db_session.query(User).filter_by(username=test_username).first():
            return test_username

    return None


def validate_and_generate_username(username=None, name=None, user_id=None, db_session=None):
    """
    Comprehensive username validation and generation function

    Args:
        username (str, optional): Provided username
        name (str, optional): User's name for generation
        user_id (str, optional): Current user ID for updates
        db_session: Database session for uniqueness checks

    Returns:
        dict: Result with 'success' (bool), 'username' (str), and 'message' (str)
    """
    result = {
        'success': False,
        'username': None,
        'message': ''
    }

    # If username is provided, validate it
    if username:
        if not is_valid_username(username):
            result['message'] = "Invalid username format. Username must be 3-30 characters and contain only letters, numbers, underscores, and hyphens."
            return result

        # Check if username is already taken by another user
        if db_session:
            from app.models.user import User
            existing_user = db_session.query(
                User).filter_by(username=username).first()
            if existing_user and (not user_id or str(existing_user.id) != str(user_id)):
                result['message'] = f"Username '{username}' is already taken."
                return result

        result['username'] = username
        result['success'] = True
        return result

    # Generate username from name
    if name:
        generated_username = generate_unique_username(
            name, db_session=db_session)
        if generated_username:
            result['username'] = generated_username
            result['success'] = True
            return result
        else:
            result['message'] = "Could not generate a unique username from the provided name."
            return result

    # Fallback: generate generic username
    generic_username = generate_unique_username('user', db_session=db_session)
    if generic_username:
        result['username'] = generic_username
        result['success'] = True
        return result

    result['message'] = "Failed to generate a valid username."
    return result


def update_user_username(user, new_username, db_session=None):
    """
    Update a user's username with validation

    Args:
        user (User): User object to update
        new_username (str): New username
        db_session: Database session

    Returns:
        dict: Result with 'success' (bool), 'username' (str), and 'message' (str)
    """
    result = validate_and_generate_username(
        username=new_username,
        user_id=str(user.id),
        db_session=db_session
    )

    if result['success']:
        try:
            user.username = result['username']
            user.save()
            return result
        except Exception as e:
            result['success'] = False
            result['message'] = f"Failed to update username: {str(e)}"
            return result

    return result


def check_username_availability(username, db_session=None):
    """
    Check if a username is available

    Args:
        username (str): Username to check
        db_session: Database session for checking

    Returns:
        dict: Result with 'available' (bool) and 'message' (str)
    """
    result = {
        'available': False,
        'message': ''
    }

    if not is_valid_username(username):
        result['message'] = "Invalid username format."
        return result

    if db_session:
        from app.models.user import User
        existing_user = db_session.query(
            User).filter_by(username=username).first()
        if existing_user:
            result['message'] = f"Username '{username}' is already taken."
            return result

    result['available'] = True
    result['message'] = f"Username '{username}' is available."
    return result
