from datetime import datetime, timedelta
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import text as sa_text
from sqlalchemy.orm import relationship, backref
from app.models import db
from app.models.model_mixin import ModelMixin


class Project(ModelMixin):
    __tablename__ = 'project'
    id = db.Column(UUID(as_uuid=True), primary_key=True, server_default=sa_text("uuid_generate_v4()"))
    name = db.Column(db.String(256), nullable=True)
    alias = db.Column(db.String(256), nullable=False, unique=True)
    owner_id = db.Column(UUID(as_uuid=True), db.ForeignKey('user.id'), nullable=False)
    cluster_id = db.Column(UUID(as_uuid=True), db.ForeignKey('clusters.id'), nullable=False)
    apps = db.relationship('App', backref='project', lazy=True)
    description = db.Column(db.String, nullable=True)
    date_created = db.Column(db.DateTime, default=db.func.current_timestamp())
    project_databases = db.relationship(
        'ProjectDatabase', backref='project', lazy=True)
