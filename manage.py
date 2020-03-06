from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand
from app.models import db
from server import app

# import models
from app.helpers.admin import create_superuser, create_default_roles
from app.models.user import User
from app.models.user_role import UserRole
from app.models.organisation import Organisation
from app.models.organisation_members import OrganisationMembers
from app.models.organisation_admins import OrganisationAdmins
from app.models.clusters import Cluster
from app.models.project import Project
# from app.models.namespaces import Namespace

# register app and db with migration class
migrate = Migrate(app, db)
manager = Manager(app)

manager.add_command('db', MigrateCommand)


@manager.option('-e', '--email', dest='email')
@manager.option('-p', '--password', dest='password')
@manager.option('-c', '--confirm_password', dest='confirm_password')
def admin_user(email, password, confirm_password):
    create_superuser(email, password, confirm_password)


@manager.command
def create_roles():
    create_default_roles()

if __name__ == '__main__':
    manager.run()