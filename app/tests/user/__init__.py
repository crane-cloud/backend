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


    def create_user(self, user_data):
        user = User(email=user_data['email'], 
                    password=user_data['password'], 
                    name=user_data['name'])
        user.verified=True
        user.save()
        return user
