from itsdangerous import URLSafeTimedSerializer

from app import app


def generate_token(email):
    """ generate verification token """

    serializer = URLSafeTimedSerializer(app.config["SECRET_KEY"])
    return serializer.dumps(email, salt=app.config["PASSWORD_SALT"])


def validate_token(token, expiration=3600):
    serializer = URLSafeTimedSerializer(app.config["SECRET_KEY"])
    try:
        email = serializer.loads(
            token, salt=app.config["PASSWORD_SALT"], max_age=expiration
        )
    except:
        return False
    return email

