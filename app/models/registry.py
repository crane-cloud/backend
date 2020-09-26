from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import text as sa_text
from flask import current_app as current_app
from app.models import db
from app.models.model_mixin import ModelMixin


class Registry(ModelMixin):

    __tablename__ = 'registries'

    id = db.Column(UUID(as_uuid=True), primary_key=True, server_default=sa_text("uuid_generate_v4()"))
    name = db.Column(db.String, nullable=False, unique=True)
    date_created = db.Column(db.DateTime, default=db.func.current_timestamp())

