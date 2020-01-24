from app.models import db
from sqlalchemy.orm import relationship, backref
from app.models.user import User
from app.models.organisation import Organisation

from app.models.model_mixin import ModelMixin


class OrganisationAdmins(ModelMixin):
    _tablename_ = "organisation_admins"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column('user_id', db.Integer, db.ForeignKey(User.id, ondelete='CASCADE'), nullable=False)
    organisation_id = db.Column("organisation_id", db.Integer, db.ForeignKey(Organisation.id, ondelete='CASCADE'), nullable=False)
    user = relationship(User, backref=backref("admin_assoc"))
    organisation = relationship(Organisation, backref=backref("admin_assoc"))

    def __init__(self, user_id, organisation_id):
        """ initialize """  
        self.user_id = user_id
        self.organisation_id = organisation_id