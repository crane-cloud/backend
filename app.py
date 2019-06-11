import os

from flask import Flask

# import ORM
from flask_sqlalchemy import SQLAlchemy

# import kubernetes client
from kubernetes import client, config

# load config from file
config.load_kube_config()

# create API instance
kube_api = client.CoreV1Api()

# initialize sql-alchemy
db = SQLAlchemy()

# import blueprints
from routes.user import user_bp
from routes.admin import admin_bp

def create_app(config_name):
    """ app factory """
    
    # import config options
    from config import app_config

    app = Flask(__name__)

    # use running config settings on app
    app.config.from_object(app_config[config_name])
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # register blueprints with the app
    app.register_blueprint(user_bp)
    app.register_blueprint(admin_bp)

    # register app with the db
    db.init_app(app)

    return app

# create app instance using running config
app = create_app(os.getenv('FLASK_ENV'))

if __name__ == '__main__':
    app.run()