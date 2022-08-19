from sqlalchemy.dialects.postgresql import UUID

from app.models import transaction_record
from ..models import db
from sqlalchemy import text as sa_text

from app.models.model_mixin import ModelMixin
from app.models.billing_metrics import BillingMetrics


class BillingInvoice(ModelMixin):
    """ billing invoice table definition"""

    __tablename__ = 'billing_invoices'

    # billing invoice fields
    id = db.Column(UUID(as_uuid=True), primary_key=True, 
                    server_default=sa_text("uuid_generate_v4()"))
    display_id = db.Column(db.String, nullable=False, server_default=sa_text("concat('CC',to_char(CURRENT_DATE, 'YY'), '-', substring(uuid_generate_v4()::TEXT from 1 for 8))"))
    total_amount = db.Column(db.Integer, nullable=True, default=0.00)
    date_cashed = db.Column(db.DateTime, nullable=True)
    metrics = db.relationship('BillingMetrics', backref='invoice', lazy=True)
    transaction_record = db.relationship('TransactionRecord', backref='billing_invoice', lazy=True)
    is_cashed = db.Column(db.Boolean, nullable=False, default=False)
    project_id = db.Column(UUID(as_uuid=True), db.ForeignKey('project.id'), nullable=False)
    date_created = db.Column(db.DateTime, default=db.func.current_timestamp())
    