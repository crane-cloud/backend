from flask import current_app
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import text as sa_text
from flask_bcrypt import Bcrypt
from datetime import timedelta
from ..models import db
from app.models.model_mixin import ModelMixin


class AnonymousUser(ModelMixin):
    """ anonymous user table definition """

    _tablename_ = "anonymous_users"

    # fields of the user table
    id = db.Column(UUID(as_uuid=True), primary_key=True,
                   server_default=sa_text("uuid_generate_v4()"))
    email = db.Column(db.String(256), unique=True, nullable=False, default="")
    role = db.Column(db.String(256), nullable=False)
    project_id = db.Column(UUID(as_uuid=True), db.ForeignKey('project.id'), nullable=False)
    date_created = db.Column(db.DateTime, default=db.func.current_timestamp())

