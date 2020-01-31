from flask import current_app
from flask_bcrypt import Bcrypt
from sqlalchemy.orm import relationship
from flask_jwt_extended import create_access_token
from datetime import timedelta

from ..models import db

from app.models.model_mixin import ModelMixin


class User(ModelMixin):
    """ user table definition """

    _tablename_ = "users"

    # fields of the user table
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(256), unique=True, nullable=False, default="")
    name = db.Column(db.String(256), nullable=False, default="")
    username = db.Column(db.String(256), nullable=False, default="")
    password = db.Column(db.String(256), nullable=False, default="")
    verified = db.Column(db.Boolean, nullable=False, default=False)
    date_created = db.Column(db.DateTime, default=db.func.current_timestamp())


    def __init__(self, email, name, password):
        """ initialize with email, username and password """
        self.email = email
        self.name = name
        self.username = name
        self.password = Bcrypt().generate_password_hash(password).decode()

    def password_is_valid(self, password):
        """ checks the password against it's hash to validate the user's password """
        return Bcrypt().check_password_hash(self.password, password)

    def generate_token(self, id):
        """ generates the access token """

        # set token expiry period
        expiry = timedelta(days=10)

        return create_access_token(id, expires_delta=expiry)

    def __repr__(self):
        return "<User: {}>".format(self.email)
