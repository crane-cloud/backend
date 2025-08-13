from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import text as sa_text
from app.models import db
from app.models.model_mixin import ModelMixin, SoftDeleteQuery


class AppDomain(ModelMixin):
    __tablename__ = 'app_domain'
    query_class = SoftDeleteQuery

    id = db.Column(UUID(as_uuid=True), primary_key=True,
                   server_default=sa_text("uuid_generate_v4()"))
    app_id = db.Column(UUID(as_uuid=True), db.ForeignKey(
        'app.id'), nullable=False)
    domain = db.Column(db.String(256), nullable=False)
    is_active = db.Column(db.Boolean, nullable=False, default=False)
    is_generated = db.Column(db.Boolean, nullable=False, default=False)
    date_created = db.Column(db.DateTime, default=db.func.current_timestamp())
    deleted = db.Column(db.Boolean, default=False)
    
    app = db.relationship("App", backref='domains', lazy=True)