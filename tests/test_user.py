import unittest
import json

from app import create_app, db

class UserTestCase(unittest.TestCase):
    """ user test case """

    def setUp(self):
        """ define test variables and initialize app """

        self.app = create_app('testing')
        self.client = self.app.test_client
        
        self.test_user = {
            'email': 'test_email@test_domain',
            'password': 'test_password'
        }

        with self.app.app_context():
            """ bind app to current context """

            # create all tables
            db.create_all()

    def test_sign_up(self):
        """ test user creation """

        response = self.client().post('/signup/', data=self.test_user)

        self.assertEqual(response.status_code, 201)
        self.assertIn('test_email@test_domain', str(response.data))

    def tearDown(self):
        """ destroy created data """

        with self.app.app_context():
            db.session.remove()
            db.drop_all()

if __name__ == 'main':
    unittest.main()