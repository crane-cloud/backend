import enum
from app.models import db
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import text as sa_text
# from app.models.user import User
# from app.models.project import Project
from app.models.model_mixin import ModelMixin

class RolesList(enum.Enum):
    owner = "owner"
    admin = "admin"
    member = "member"

class ProjectUser(ModelMixin):
    _tablename_ = "project_users"

    id = db.Column(UUID(as_uuid=True), primary_key=True, server_default=sa_text("uuid_generate_v4()"))
    # user_id = db.Column('user_id', UUID(as_uuid=True), db.ForeignKey(User.id), nullable=False)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('user.id'), nullable=False)
    project_id = db.Column(UUID(as_uuid=True), db.ForeignKey('project.id'), nullable=False)
    role = db.Column(db.Enum(RolesList), nullable=False)
    accepted_collaboration_invite = db.Column(db.Boolean, nullable=True)
    user = db.relationship("User", back_populates="other_projects")
    other_project = db.relationship("Project", back_populates="users")



class ProjectFollowers(ModelMixin):
    _tablename_ = "project_followers"

    id = db.Column(UUID(as_uuid=True), primary_key=True, server_default=sa_text("uuid_generate_v4()"))
    # user_id = db.Column('user_id', UUID(as_uuid=True), db.ForeignKey(User.id), nullable=False)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('user.id'), nullable=False)
    project_id = db.Column(UUID(as_uuid=True), db.ForeignKey('project.id'), nullable=False)

    user = db.relationship("User", back_populates="followed_projects")
    project = db.relationship("Project", back_populates="followers")

    