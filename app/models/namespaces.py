
import jwt

from datetime import datetime, timedelta

from app.models.organisation import Organisation

from app.models import db
from app.models.model_mixin import ModelMixin

from app.helpers.toDict import ToDict


class Namespace(ModelMixin):
    """ Namespace table definition """

    _tablename_ = 'namespace'
    __table_args__ = (db.UniqueConstraint('name', name='namespace_unique_name'),)

    # fields of the Namespace table
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256), nullable=False)
    organisation_id = db.Column("organisation_id", db.Integer, db.ForeignKey(Organisation.id, ondelete='CASCADE'))
    date_created = db.Column(db.DateTime, default=db.func.current_timestamp())

    def __init__(self, name, organisation_id):
        """ initialize with name and org_id """
        self.name = name
        self.organisation_id = organisation_id
