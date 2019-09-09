import os


class All:
    """ parent config """

    JWT_SECRET_KEY = os.getenv("FLASK_APP_SECRET")
    PASSWORD_SALT = os.getenv("FLASK_APP_SALT")


class Development(All):
    """ development config """
    
    DEBUG = (True,)
    SQLALCHEMY_DATABASE_URI = "postgresql:///cranecloud"

class Testing(All):
    """ test environment config """

    TESTING = (True,)
    DEBUG = (True,)
    # use a separate db
    
    SQLALCHEMY_DATABASE_URI = "postgresql:///cranecloud_test_db"

class Production(All):
    """ production config """

    DEBUG = (False,)
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URI")


app_config = {"development": Development, "testing": Testing, "production": Production}

