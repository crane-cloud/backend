import os
from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand

# import config options
from config import app_config

from app import app, db

import models

# get the running config
config_name = os.getenv('FLASK_APP_CONFIG')

# use running config settings on app
app.config.from_object(app_config[config_name])
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# add db wrapper
db.init_app(app)

migrate = Migrate(app, db)
manager = Manager(app)

manager.add_command('db', MigrateCommand)

if __name__ == '__main__':
    manager.run()