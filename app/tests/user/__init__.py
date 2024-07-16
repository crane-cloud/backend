from app.models.role import Role
from app.models.user import User


class UserBaseTestCase():
    user_data = {
        'email': 'rhodin@cranecloud.io',
        'name': 'Test User',
        'password': 'Compl3xPassw0rd',
        'organisation': 'Makerere',
        'phone_number': '+256777777777'
        }
    user_data_2 = {
        'email': 'henry@cranecloud.io',
        'name': 'Test User 2',
        'organisation': 'Makerere',
        'password': 'Compl3xPassw0rd',
    }
    invalid_user_data = {
        'emails': 'test_email@testdomain',
        'name': 'Test User',
        'passwords': 'wrong_password',
    }
    
    admin_data = {
        'email': 'admin@cranecloud.io',
        'name': 'Test Admin',
        'password': 'Compl3xPassw0rd',
        'phone_number': '+256777777777',
        'organisation': 'Makerere',
    }

    def create_user(self, user_data):
        user = User(email=user_data['email'],
                    organisation=user_data['organisation'], 
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
