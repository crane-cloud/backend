from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import text as sa_text
from app.models import db
from app.models.model_mixin import ModelMixin
from flask_bcrypt import Bcrypt


class ProjectDatabase(ModelMixin):
    __tablename__ = 'project_database'
    id = db.Column(UUID(as_uuid=True), primary_key=True,
                   server_default=sa_text("uuid_generate_v4()"))
    host = db.Column(db.String(256), nullable=True)
    name = db.Column(db.String(256), nullable=False)
    user = db.Column(db.String(256), nullable=False)
    password = db.Column(db.String(256), nullable=False)
    project_id = db.Column(UUID(as_uuid=True), db.ForeignKey(
        'project.id'))
    date_created = db.Column(db.DateTime, default=db.func.current_timestamp())

    def __init__(self, **kwargs):
        self.user = kwargs['user']
        self.host = kwargs['host']
        self.name = kwargs['name']
        self.password = Bcrypt().generate_password_hash(
            kwargs['password']).decode()

    def password_is_valid(self, password):
        """ checks the password against it's hash to validate the user's password """
        return Bcrypt().check_password_hash(self.password, password)
