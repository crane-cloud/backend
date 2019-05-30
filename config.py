import os

class All():
    """ parent config """
    APP_SECRET = os.getenv('FLASK_APP_SECRET')

class Development(All):
    """ development config """
    DEBUG = True,
    SQLALCHEMY_DATABASE_URI = 'postgresql://localhost/osprey'

class Production(All):
    """ production config """
    DEBUG = False,
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URI')

app_config = {
    'development': Development,
    'production': Production
}