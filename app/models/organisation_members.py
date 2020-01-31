from app.models import db
from app.models.user import User
from sqlalchemy.orm import relationship, backref
from app.models.organisation import Organisation

from app.models.model_mixin import ModelMixin


class OrganisationMembers(ModelMixin):

    _tablename_ = "organisation_members"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column('user_id', db.Integer, db.ForeignKey(User.id, ondelete='CASCADE'), nullable=False)
    organisation_id = db.Column("organisation_id", db.Integer, db.ForeignKey(Organisation.id, ondelete='CASCADE'), nullable=False)
