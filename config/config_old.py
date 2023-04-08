import os


class Base:
    """ base config """

    # main
    SECRET_KEY = os.getenv("FLASK_APP_SECRET")
    PASSWORD_SALT = os.getenv("FLASK_APP_SALT")
    VERIFICATION_SALT = os.getenv("FLASK_VERIFY_SALT")

    # mail settings
    MAIL_SERVER = "smtp.gmail.com"
    MAIL_PORT = 465
    MAIL_USE_TLS = False
    MAIL_USE_SSL = True

    # gmail authentication
    MAIL_USERNAME = os.getenv("APP_MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("APP_MAIL_PASSWORD")

    # mail accounts
    MAIL_DEFAULT_SENDER = "no-reply@cranecloud.io"


class Development(Base):
    """ development config """

    DEBUG = True
    SQLALCHEMY_DATABASE_URI = "postgresql://postgres:postgres@database/cranecloud2"


class Testing(Base):
    """ test environment config """

    TESTING = True
    DEBUG = True
    # use a separate db

    SQLALCHEMY_DATABASE_URI = "postgresql:///cranecloud2"


class Production(Base):
    """ production config """

    DEBUG = (False,)
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URI")


app_config = {"development": Development, "testing": Testing, "production": Production}
