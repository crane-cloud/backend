import jwt

from datetime import datetime, timedelta
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import text as sa_text

#from app.models.organisation import Organisation

from app.models import db
from app.models.model_mixin import ModelMixin

from app.helpers.toDict import ToDict


class Namespace(ModelMixin):
    """ Namespace table definition """

    _tablename_ = 'namespace'
    __table_args__ = (db.UniqueConstraint('name', name='namespace_unique_name'),)

    # fields of the Namespace table
    id = db.Column(UUID(as_uuid=True), primary_key=True, server_default=sa_text("uuid_generate_v4()"))
    name = db.Column(db.String(256), nullable=False)
    #organisation_id = db.Column("organisation_id", UUID(as_uuid=True), db.ForeignKey(Organisation.id, ondelete='CASCADE'))
    date_created = db.Column(db.DateTime, default=db.func.current_timestamp())

    def __init__(self, name):
        """ initialize with name """
        self.name = name
        #self.organisation_id = organisation_id