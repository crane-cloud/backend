from os.path import join, dirname
from dotenv import load_dotenv
from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand
from app.models import db
from server import app

# import models
from app.helpers.admin import create_superuser, create_default_roles
from app.helpers.registry import add_registries
from app.models.user import User
from app.models.user_role import UserRole
from app.models.clusters import Cluster
from app.models.project import Project
from app.models.app import App
from app.models.project_database import ProjectDatabase
from app.models.billing_invoice import BillingInvoice
from app.models.user_payment import UserPaymentDetails
from app.models.billing_metrics import BillingMetrics
from app.models.transaction_record import TransactionRecord
from app.models.credits import Credit
from app.models.credit_assignments import CreditAssignment

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

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


@manager.command
def create_registries():
    add_registries()


if __name__ == '__main__':
    manager.run()
