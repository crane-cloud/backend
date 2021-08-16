from itsdangerous import URLSafeTimedSerializer


def generate_token(email, secret_key, password_salt):
    """ generate verification token """

    serializer = URLSafeTimedSerializer(secret_key)
    return serializer.dumps(email, salt=password_salt)


def validate_token(token, secret_key, password_salt, expiration=86400):
    serializer = URLSafeTimedSerializer(secret_key)
    try:
        email = serializer.loads(
            token, salt=password_salt, max_age=expiration
        )
    except Exception:
        return False
    return email
