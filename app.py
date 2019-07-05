import os

from flask import Flask

# import ORM
from flask_sqlalchemy import SQLAlchemy

# import migration class
from flask_migrate import Migrate

# import kubernetes client
from kubernetes import client

# configure client
config = client.Configuration()
config.host = os.getenv('KUBE_HOST')
config.api_key['authorization'] = os.getenv('KUBE_TOKEN')
config.api_key_prefix['authorization'] = 'Bearer'
config.verify_ssl = False

# create API instance
kube = client.CoreV1Api(client.ApiClient(config))

# initialize sql-alchemy
db = SQLAlchemy()

# import blueprints
from routes.user import user_bp
from routes.admin import admin_bp
from routes.monitoring import monitor_bp

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
    app.register_blueprint(monitor_bp)

    # register app with the db
    db.init_app(app)

    # register app and db with migration class
    Migrate(app, db)

    # import models
    from models.user import User
    from models.admin import Admin

    return app

# create app instance using running config
app = create_app(os.getenv('FLASK_ENV'))

if __name__ == '__main__':
    app.run()
