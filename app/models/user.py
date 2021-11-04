from flask import current_app
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import text as sa_text
from flask_bcrypt import Bcrypt
from flask_jwt_extended import create_access_token
from datetime import timedelta

from ..models import db

from app.models.model_mixin import ModelMixin


class User(ModelMixin):
    """ user table definition """

    _tablename_ = "users"

    # fields of the user table
    id = db.Column(UUID(as_uuid=True), primary_key=True,
                   server_default=sa_text("uuid_generate_v4()"))
    email = db.Column(db.String(256), unique=True, nullable=False, default="")
    name = db.Column(db.String(256), nullable=False, default="")
    username = db.Column(db.String(256), nullable=False, default="")
    password = db.Column(db.String(256), nullable=False, default="")
    verified = db.Column(db.Boolean, nullable=False, default=False)
    date_created = db.Column(db.DateTime, default=db.func.current_timestamp())
    projects = db.relationship('Project', backref='owner', lazy=True)
    is_beta_user = db.Column(db.Boolean, nullable=False, default=False)

    def __init__(self, email, name, password):
        """ initialize with email, username and password """
        self.email = email
        self.name = name
        self.username = name
        self.password = Bcrypt().generate_password_hash(password).decode()

    def password_is_valid(self, password):
        """ checks the password against it's hash to validate the user's password """
        return Bcrypt().check_password_hash(self.password, password)

    def generate_token(self, user):
        """ generates the access token """

        # set token expiry period
        expiry = timedelta(days=10)

        return create_access_token(user, expires_delta=expiry)

    def __repr__(self):
        return "<User: {}>".format(self.email)
