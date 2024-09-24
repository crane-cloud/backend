from sqlalchemy.dialects.postgresql import UUID
from app.models import db
from app.models.model_mixin import ModelMixin, SoftDeleteQuery
from sqlalchemy import text as sa_text


class Tag(ModelMixin):
    __tablename__ = "tag"
    query_class = SoftDeleteQuery

    id = db.Column(UUID(as_uuid=True), primary_key=True,
                   server_default=sa_text("uuid_generate_v4()"))
    name = db.Column(db.String)
    deleted = db.Column(db.Boolean, default=False)
    is_super_tag = db.Column(db.Boolean, default=False)
    projects = db.relationship("ProjectTag", back_populates="tag")
    date_created = db.Column(db.DateTime, default=db.func.current_timestamp())
    followers = db.relationship('TagFollowers', back_populates='tag')

    def __repr__(self):
        return f"<Tag {self.name}>"



class ProjectTag(ModelMixin):
    __tablename__ = "project_tag"

    id = db.Column(UUID(as_uuid=True), primary_key=True,
                   server_default=sa_text("uuid_generate_v4()"))
    project_id = db.Column(UUID(as_uuid=True), db.ForeignKey("project.id"))
    tag_id = db.Column(UUID(as_uuid=True), db.ForeignKey("tag.id"))

    date_created = db.Column(db.DateTime, default=db.func.current_timestamp())
    project = db.relationship("Project", back_populates="tags")
    tag = db.relationship("Tag", back_populates="projects")

    def __repr__(self):
        return f"<ProjectTag {self.project.name}, {self.tag.name}>"


class TagFollowers(ModelMixin):
    _tablename_ = "tag_followers"

    id = db.Column(UUID(as_uuid=True), primary_key=True,
                   server_default=sa_text("uuid_generate_v4()"))
    user_id = db.Column('user_id', UUID(as_uuid=True),
                        db.ForeignKey('user.id'), nullable=False)
    tag_id = db.Column(UUID(as_uuid=True),
                       db.ForeignKey('tag.id'), nullable=False)
    date_created = db.Column(db.DateTime, default=db.func.current_timestamp())
    user = db.relationship("User", back_populates="followed_tags")
    tag = db.relationship("Tag", back_populates="followers")
