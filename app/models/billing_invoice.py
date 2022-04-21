from sqlalchemy.dialects.postgresql import UUID
from ..models import db
from sqlalchemy import text as sa_text

from app.models.model_mixin import ModelMixin


class BillingInvoice(ModelMixin):
    """ billing invoice table definition"""

    __tablename__ = 'billing_invoices'

    # billing invoice fields
    id = db.Column(UUID(as_uuid=True), primary_key=True, 
                    server_default=sa_text("uuid_generate_v4()"))
    total_amount = db.Column(db.Integer, nullable=True, default=0.00)
    date_cashed = db.Column(db.DateTime)
    is_cashed = db.Column(db.Boolean, nullable=False, default=False)
    project_id = db.Column(UUID(as_uuid=True), db.ForeignKey('project.id'), nullable=False)
    # date_created = db.Column(db.DateTime, default=db.func.current_timestamp())
    