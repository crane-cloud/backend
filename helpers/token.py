from itsdangerous import URLSafeTimedSerializer

from flask import current_app


def generate_token(email):
    """ generate verification token """

    serializer = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    return serializer.dumps(email, salt=current_app.config["PASSWORD_SALT"])


def validate_token(token, expiration=3600):
    serializer = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    try:
        email = serializer.loads(
            token, salt=current_app.config["PASSWORD_SALT"], max_age=expiration
        )
    except:
        return False
    return email

