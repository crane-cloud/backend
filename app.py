import os

from flask import Flask

# import ORM
from flask_sqlalchemy import SQLAlchemy

# initialize sql-alchemy
db = SQLAlchemy()

def create_app():
    """ create app instance """
    # import config options
    from config import app_config

    # get the running config
    config_name = os.getenv('FLASK_APP_CONFIG')

    app = Flask(__name__)

    # use running config settings on app
    app.config.from_object(app_config[config_name])
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # add db wrapper
    db.init_app(app)

    return app

app = create_app()

# import routes
import router

if __name__ == '__main__':
    app.run()