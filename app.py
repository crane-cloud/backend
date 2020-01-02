import os

from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager

# import ORM
from flask_sqlalchemy import SQLAlchemy

# import kubernetes client
from kubernetes import client

from flask_mail import Mail

# configure client
config = client.Configuration()
config.host = os.getenv('KUBE_HOST')
config.api_key['authorization'] = os.getenv('KUBE_TOKEN')
config.api_key_prefix['authorization'] = 'Bearer'
config.verify_ssl = False

# create API instance
kube = client.CoreV1Api(client.ApiClient(config))
extension_api = client.ExtensionsV1beta1Api(client.ApiClient(config))
appsv1_api = client.AppsV1Api(client.ApiClient(config))

# initialize sql-alchemy
db = SQLAlchemy()

my_app = ''

# import blueprints
from routes.user import user_bp
from routes.admin import admin_bp
from routes.organisation_members import organisation_members_bp
from routes.organisation import organisation_bp
from routes.monitoring import monitor_bp
from routes.deployment import deployment_bp
from routes.namespaces import namespace_bp
#from routes.organisation import organisation_bp

mail = Mail()
food = "my food"

def create_app(config_name):
    """ app factory """
    
    # import config options
    from config import app_config

    app = Flask(__name__)

    # allow cross-domain requests
    CORS(app)

    # use running config settings on app
    app.config.from_object(app_config[config_name])
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # register blueprints with the app
    app.register_blueprint(user_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(organisation_members_bp)
    app.register_blueprint(organisation_bp)
    app.register_blueprint(namespace_bp)
    app.register_blueprint(monitor_bp)
    app.register_blueprint(deployment_bp)
   # app.register_blueprint(organisation_bp)

    # register app with the db
    db.init_app(app)

    # mail.init_app(app)
    mail.init_app(app)
    
    # initialize jwt with app
    JWTManager(app)
    
    return app

# create app instance using running config
app = create_app(os.getenv('FLASK_ENV'))
# email_sender = app.config["MAIL_DEFAULT_SENDER"]
my_app = app

if __name__ == '__main__':
    app.run()
