from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import text as sa_text
from app.models import db
from app.models.user import User
from app.models.organisation import Organisation

from app.models.model_mixin import ModelMixin


class OrganisationAdmins(ModelMixin):
    _tablename_ = "organisation_admins"

    id = db.Column(UUID(as_uuid=True), primary_key=True, server_default=sa_text("uuid_generate_v4()"))
    user_id = db.Column('user_id', UUID(as_uuid=True), db.ForeignKey(User.id, ondelete='CASCADE'), nullable=False)
    organisation_id = db.Column("organisation_id", UUID, db.ForeignKey(Organisation.id, ondelete='CASCADE'), nullable=False)