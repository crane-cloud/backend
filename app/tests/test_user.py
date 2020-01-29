import unittest

from server import create_app
from app.models import db

class UserTestCase(unittest.TestCase):
    """ user test case """

    def setUp(self):
        """ executed before each test """

        # define test variables and initialize app
        self.app = create_app('testing')
        self.client = self.app.test_client()
        
        self.test_user = {
            'email': 'test_email@testdomain.com',
            'name': 'test_name',
            'password': 'test_password'
        }

        with self.app.app_context():
            """ bind app to current context """

            # create all tables
            db.create_all()

    def tearDown(self):
        """ executed after each test """

        # destroy created data
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_sign_up(self):
        """ test user creation """

        response = self.client.post('/users', json=self.test_user)

        # self.assertEqual(response.status_code, 201)
        self.assertIn('test_email@testdomain.com', str(response.data))
        self.assertIn('test_name', str(response.data))

if __name__ == 'main':
    unittest.main()