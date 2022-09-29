import os
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import text as sa_text
from sqlalchemy_utils import EncryptedType
from app.models import db
from app.models.model_mixin import ModelMixin

secret = os.getenv('FLASK_APP_SECRET')


class Cluster(ModelMixin):

    __tablename__ = 'clusters'

    id = db.Column(UUID(as_uuid=True), primary_key=True,
                   server_default=sa_text("uuid_generate_v4()"))
    name = db.Column(db.String, nullable=False, unique=True)
    host = db.Column(db.String, nullable=False, unique=True)
    token = db.Column(EncryptedType(db.String, secret), nullable=False)
    description = db.Column(db.String, nullable=False)
    prometheus_url = db.Column(db.String, default="")
    cost_modal_url = db.Column(db.String, default="")
    projects = db.relationship('Project', backref='cluster', lazy=True)
    date_created = db.Column(db.DateTime, default=db.func.current_timestamp())
