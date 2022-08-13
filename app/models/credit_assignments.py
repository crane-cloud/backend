from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import text as sa_text
from app.models import db
from app.models.model_mixin import ModelMixin

class CreditAssignment(ModelMixin):
    __tablename__ = 'credit_assignments'
    id = db.Column(UUID(as_uuid=True), primary_key=True, server_default=sa_text("uuid_generate_v4()"))
    amount = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String, nullable=True)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('user.id'), nullable=False)
    date_created = db.Column(db.DateTime, default=db.func.current_timestamp())