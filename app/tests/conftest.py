import os
from types import SimpleNamespace
from app.helpers.admin import create_default_roles
from app.schemas.user import UserSchema
from app.tests.user import UserBaseTestCase
from sqlalchemy import text
import pytest
import logging

from app.models.user import User
from server import create_app, db


user_data = {
    "email": "test_email@testdomain.com",
    "name": "test_name",
    "password": "test_password",
    "organisation": "Makerere"
}

@pytest.fixture(scope='function')
def new_user(test_client):
    user = User(**user_data)
    user.verified = True
    user.save()
    return user


@pytest.fixture(scope='function')
def test_client():
    flask_app = create_app(config_name='testing')
    flask_app.config['SECRET_KEY'] = "192b9bdd22ab9ed4d12e236c78afcb9a393ec15f71bbf5dc987d54727823bcbf"

    with flask_app.test_client() as testing_client:
        with flask_app.app_context():
            db.create_all()
            create_default_roles()
            yield testing_client
            db.session.remove()
            db.drop_all()


@pytest.fixture(scope='function')
def login_user(test_client):
    user_client = UserBaseTestCase()
    user = user_client.create_user(user_client.user_data)
    token_schema = UserSchema()
    user_dict = token_schema.dump(user)
    access_token = user.generate_token(user_dict)
    return SimpleNamespace(headers={'Authorization': f'Bearer {access_token}'}, user=user)

@pytest.fixture(scope='function')
def admin_login_user(test_client):
    user_client = UserBaseTestCase()
    admin = user_client.create_admin(user_client.admin_data)
    token_schema = UserSchema()
    user_dict = token_schema.dump(admin)
    access_token = admin.generate_token(user_dict)
    return SimpleNamespace(headers={'Authorization': f'Bearer {access_token}'}, admin=admin)
