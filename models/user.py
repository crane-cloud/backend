import jwt
from datetime import datetime, timedelta

from flask import current_app
from flask_bcrypt import Bcrypt

from app import db

class User(db.Model):
    """ user table definition """

    _tablename_ = 'users'

    # fields of the user table
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(256), nullable=False, default='')
    name = db.Column(db.String(256), nullable=False, default='')
    username = db.Column(db.String(256), nullable=False, default='')
    password = db.Column(db.String(256), nullable=False, default='')
    date_created = db.Column(db.DateTime, default=db.func.current_timestamp())

    def __init__(self, email, name, password):
        """ initialize with email, username and password """
        self.email = email
        self.name = name
        self.password = Bcrypt().generate_password_hash(password).decode()

    def password_is_valid(self, password):
        """ checks the password against it's hash to validate the user's password """
        return Bcrypt().check_password_hash(self.password, password)

    def save(self):
        """
        save a user to the database
        this includes creating a new user and editing one.
        """
        db.session.add(self)
        db.session.commit()

    def generate_token(self, id):
        """ generates the access token """

        try:
            # setup a payload with an expiration time
            payload = {
                'exp': datetime.utcnow() + timedelta(minutes=3600),
                'iat': datetime.utcnow(),
                'sub': id
            }

            # create the bytestring token using the payload and the secret key
            jwt_string = jwt.encode(
                payload,
                current_app.config.get('APP_SECRET'),
                algorithm='HS256'
            )

            return jwt_string

        except Exception as e:
            # return an error in string format if an exception occurs
            return str(e)

    @staticmethod
    def decode_token(token):
        """ decodes the access token from then authorization header """
        try:
            # try to decode the token using our secret variables
            payload = jwt.decode(token, current_app.config.get('APP_SECRET'))
            return payload['sub']

        except jwt.ExpiredSignatureError:
            # the token is expired, return an error string
            return "Expired token. Please login to get a new token"

        except jwt.InvalidTokenError:
            # the token is invalid, return an error string
            return "Invalid token. Please register or login"

    def __repr__(self):
        return "<User: {}>".format(self.email)