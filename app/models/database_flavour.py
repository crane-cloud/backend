from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import text as sa_text
from app.models import db
from app.models.model_mixin import ModelMixin
from flask_bcrypt import Bcrypt


class DatabaseFlavour(ModelMixin):
    __tablename__ = 'database_flavour'
    id = db.Column(UUID(as_uuid=True), primary_key=True,
                   server_default=sa_text("uuid_generate_v4()"))
    name = db.Column(db.String(256), nullable=False)
    date_created = db.Column(db.DateTime, default=db.func.current_timestamp())
    project_databases = db.relationship(
        'ProjectDatabase', backref='database_flavour', lazy=True)
