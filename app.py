import os

from flask import Flask, Blueprint

# import ORM
from flask_sqlalchemy import SQLAlchemy

# initialize sql-alchemy
db = SQLAlchemy()

def create_app(config_name):
    """ app factory """
    
    # import config options
    from config import app_config

    app = Flask(__name__)

    # use running config settings on app
    app.config.from_object(app_config[config_name])
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # register app with the db
    db.init_app(app)

    return app

# create app instance using running config
app = create_app(os.getenv('FLASK_ENV'))

import routes

if __name__ == '__main__':
    app.run()