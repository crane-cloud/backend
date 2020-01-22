from app.models import db
from app.models.user import User
from app.models.role import Role
from app.models.model_mixin import ModelMixin


class UserRole(ModelMixin):
    _tablename_ = "user_roles"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column('user_id', db.Integer, db.ForeignKey(User.id, ondelete='CASCADE'), nullable=False)
    role_id = db.Column("role_id", db.Integer, db.ForeignKey(Role.id, ondelete='CASCADE'), nullable=False)

    def __init__(self, user_id, role_id):
        self.user_id = user_id
        self.role_id = role_id