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

    # EXCEPTIONS 
    PROPAGATE_EXCEPTIONS = True

    # Github auth
    GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
    GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")


class Development(Base):
    """ development config """

    DEBUG = True

    SQLALCHEMY_DATABASE_URI = os.getenv("LOCAL_DATABASE_URI") or "postgresql:///cranecloud"


class Testing(Base):
    """ test environment config """

    TESTING = True
    DEBUG = True
    # use a separate db

    SQLALCHEMY_DATABASE_URI = os.getenv("TEST_DATABASE_URI") or "postgresql:///cranecloud_test_db"


class Staging(Base):
    """ Staging config """

    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URI")


class Production(Base):
    """ production config """

    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URI")


app_config = {"development": Development, "testing": Testing, "staging": Staging, "production": Production}
