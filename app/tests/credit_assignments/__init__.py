from app.models.user import User
from app.helpers.admin import create_superuser

class UserBaseTestCase():
    user_data = {
        'email': 'test_email@testdomain.com',
        'name': 'Test User',
        'password': 'Compl3xPassw0rd',
        'phone_number': '+256777777777'
        }
    admin_user_data = {
        'email': 'admin@mail.com',
        'name': 'Admin User',
        'password': 'admin',
    }

    def create_user(self, user_data):
        user = User(email=user_data['email'], 
                    password=user_data['password'], 
                    name=user_data['name'])
        user.verified=True
        user.save()
        return user

class AdminUserBaseTestCase():
    admin_user_data = {
        'email': 'admin@mail.com',
        'name': 'Admin User',
        'password': 'admin',
    }

    def create_admin_user(self, admin_user_data):
        create_superuser(admin_user_data['email'],admin_user_data['password'],admin_user_data['password'])