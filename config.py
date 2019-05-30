import os

class Development():
    """ development config """
    DEBUG = True,
    SQLALCHEMY_DATABASE_URI = 'postgresql://localhost/osprey'

class Production():
    """ production config """
    DEBUG = False,
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URI')

app_config = {
    'development': Development,
    'production': Production
}