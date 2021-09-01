import jwt
from datetime import datetime, timedelta
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import text as sa_text
from app.models import db

from sqlalchemy.orm import relationship, backref

from app.models.model_mixin import ModelMixin


class Organisation(ModelMixin):
    """ Organisation table definition """

    _tablename_ = 'organisations'
    __table_args__ = (db.UniqueConstraint('name', name='organisation_unique_name'),)

    # fields of the Organisation table
    id = db.Column(UUID(as_uuid=True), primary_key=True, server_default=sa_text("uuid_generate_v4()"))
    name = db.Column(db.String(256), nullable=False)
    date_created = db.Column(db.DateTime, default=db.func.current_timestamp())
    admins = relationship('User', secondary='organisation_admins', backref='organisation_admin')
    members = relationship('User', secondary='organisation_members', backref='organisations')

    def __init__(self, name):
        """ initialize with name, member and namespace """
        self.name = name
