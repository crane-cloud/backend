from app.models import db
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, backref
from app.models.user import User
from app.models.role import Role
from app.models.model_mixin import ModelMixin


class UserRole(ModelMixin):
    _tablename_ = "user_roles"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column('user_id', UUID(as_uuid=True), db.ForeignKey(User.id))
    role_id = db.Column("role_id", UUID(as_uuid=True), db.ForeignKey(Role.id))
