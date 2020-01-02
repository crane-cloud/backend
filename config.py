import os


class Base:
    """ base config """

    # main
    SECRET_KEY = os.getenv("FLASK_APP_SECRET")
    PASSWORD_SALT = os.getenv("FLASK_APP_SALT")

    # mail settings
    MAIL_SERVER = "smtp.googlemail.com"
    MAIL_PORT = 465
    MAIL_USE_TLS = False
    MAIL_USE_SSL = True
    MAIL_DEBUG = True

    # gmail authentication
    MAIL_USERNAME = os.getenv("APP_MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("APP_MAIL_PASSWORD")

    # mail accounts
    MAIL_DEFAULT_SENDER = "no-reply@cranecloud.io"


class Development(Base):
    """ development config """

    DEBUG = (True,)
    SQLALCHEMY_DATABASE_URI = "postgresql+psycopg2://postgres:donthack@localhost:5432/cranecloud"
    # These help incase we have tests as well
    # And to help application know it surely should
    # send the emails not to mention incase of debugging 
    # unseen errors we can have a "stdout" that outputs
    # the success or failings of this feature
    TESTING = False
    # this is super crucial during testing
    MAIL_SUPPRESS_SEND = False


class Testing(Base):
    """ test environment config """

    TESTING = (True,)
    DEBUG = (True,)
    # use a separate db

    SQLALCHEMY_DATABASE_URI = "postgresql:///cranecloud_test_db"


class Production(Base):
    """ production config """

    DEBUG = (False,)
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URI")


app_config = {"development": Development, "testing": Testing, "production": Production}

