from app.models.role import Role
from app.models.user import User


class UserBaseTestCase():
    user_data = {
        'email': 'test_email@testdomain.com',
        'name': 'Test User',
        'password': 'Compl3xPassw0rd',
        'phone_number': '+256777777777'
        }
    user_data_2 = {
        'email': 'test_email_2@testdomain.com',
        'name': 'Test User 2',
        'password': 'Compl3xPassw0rd',
    }
    invalid_user_data = {
        'emails': 'test_email@testdomain',
        'name': 'Test User',
        'passwords': 'wrong_password',
    }
    admin_data = {
        'email': 'test_admin@testdomain.com',
        'name': 'Test Admin',
        'password': 'Compl3xPassw0rd',
        'phone_number': '+256777777777'
    }

    def create_user(self, user_data):
        user = User(email=user_data['email'], 
                    password=user_data['password'], 
                    name=user_data['name'])
        user.verified=True
        user.save()
        return user
    
    def create_admin(self, admin_data):
        admin_role = Role.find_first(**{'name': 'administrator'})
        if not admin_role:
            try:
                admin_role = Role(name='administrator')
                admin_role.save()
            except Exception as e:
                print(str(e))
                return
        admin_user = self.create_user(admin_data)
        admin_user.roles.append(admin_role)
        admin_user.save()
        return admin_user
