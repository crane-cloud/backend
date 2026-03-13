from flask import current_app
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy import text as sa_text
from flask_bcrypt import Bcrypt
from flask_jwt_extended import create_access_token
from datetime import timedelta

from ..models import db

from app.models.model_mixin import DetailedModelMixin, ModelMixin
from app.helpers.email_validator import validate_and_generate_username


class Followers(ModelMixin):
    """ followers table definition """

    _tablename_ = "followers"
    follower_id = db.Column(
        UUID(as_uuid=True), db.ForeignKey('user.id'), nullable=False, primary_key=True)
    followed_id = db.Column(
        UUID(as_uuid=True), db.ForeignKey('user.id'), nullable=False, primary_key=True)

    def __init__(self, follower_id, followed_id):
        """ initialize with follower_id and followed_id """
        self.follower_id = follower_id
        self.followed_id = followed_id


class User(DetailedModelMixin):
    """ user table definition """

    _tablename_ = "users"

    # fields of the user table
    id = db.Column(UUID(as_uuid=True), primary_key=True,
                   server_default=sa_text("uuid_generate_v4()"))
    email = db.Column(db.String(256), unique=True, nullable=False, default="")
    name = db.Column(db.String(256), nullable=False, default="")
    username = db.Column(db.String(256), unique=True,
                         nullable=False, default="")
    password = db.Column(db.String(256), nullable=False, default="")
    verified = db.Column(db.Boolean, nullable=False, default=False)
    last_seen = db.Column(db.DateTime, default=db.func.current_timestamp())
    last_reminder_sent = db.Column(db.DateTime, nullable=True)
    projects = db.relationship('Project', backref='owner', lazy=True)
    organisation = db.Column(db.String(256), nullable=True, default="")
    other_projects = db.relationship('ProjectUser', back_populates='user')
    is_beta_user = db.Column(db.Boolean, nullable=False, default=False)
    credits = db.relationship('Credit', backref='user', lazy=True)
    credit_assignments = db.relationship(
        'CreditAssignment', backref='user', lazy=True)
    followed_projects = db.relationship(
        'ProjectFollowers', back_populates='user')
    is_public = db.Column(db.Boolean, default=True)
    followed_tags = db.relationship(
        'TagFollowers', back_populates='user')
    profile_picture = db.Column(db.String(500), nullable=True, default='')
    biography = db.Column(db.String(500), nullable=True, default="")
    social_links = db.Column(JSONB, nullable=True, default={})

    def __init__(self, email, name, password, organisation=None, username=None, **kwargs):
        """ initialize with email, username and password """
        self.email = email
        self.name = name

        # Use reusable username validation function
        from app.models import db
        username_result = validate_and_generate_username(
            username=username,
            name=name,
            db_session=db.session
        )
        self.username = username_result.get('username', 'user')

        self.organisation = organisation
        self.password = Bcrypt().generate_password_hash(password).decode()

        # Handle additional fields like social_links
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def password_is_valid(self, password):
        """ checks the password against it's hash to validate the user's password """
        return Bcrypt().check_password_hash(self.password, password)

    def generate_token(self, user):
        """ generates the access token """

        # set token expiry period
        expiry = timedelta(days=10)

        return create_access_token(user, expires_delta=expiry)

    followed = db.relationship(
        'User', secondary='followers',
        primaryjoin=(Followers.follower_id == id),
        secondaryjoin=(Followers.followed_id == id),
        backref=db.backref('followers', lazy='dynamic'), lazy='dynamic'
    )

    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)

    def is_following(self, user):
        return self.followed.filter(Followers.followed_id == user.id).count() > 0

    def is_followed_by(self, user):
        return self.followers.filter(Followers.follower_id == user.id).count() > 0

    def __repr__(self):
        return "<User: {}>".format(self.email)
