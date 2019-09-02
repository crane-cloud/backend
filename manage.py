from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand
from app import db, app

# import models
from models.user import User
from models.admin import Admin
from models.organisation import Organisation
from models.organisation_members import OrganisationMembers

# register app and db with migration class
migrate = Migrate(app, db)
manager = Manager(app)

manager.add_command('db', MigrateCommand)

if __name__ == '__main__':
    manager.run()