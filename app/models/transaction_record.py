from sqlalchemy.dialects.postgresql import UUID
from ..models import db
from sqlalchemy import text as sa_text

from app.models.model_mixin import ModelMixin


class TransactionRecord(ModelMixin):
    """ billing transaction record """

    __tablename__ = 'transaction_record'

    # transaction record fields
    id = db.Column(UUID(as_uuid=True), primary_key=True, server_default=sa_text("uuid_generate_v4()"))
    owner_id = db.Column(UUID(as_uuid=True), db.ForeignKey('user.id'), nullable=False)
    project_id = db.Column(UUID(as_uuid=True), db.ForeignKey('project.id'), nullable=False)
    billing_invoice_id = db.Column(UUID(as_uuid=True), db.ForeignKey('billing_invoices.id'), nullable=True)
    amount = db.Column(db.Integer, nullable=True, default=0.00)
    currency = db.Column(db.String(256), nullable=True)
    name = db.Column(db.String(256), nullable=True)
    email = db.Column(db.String(256), unique=False, nullable=True, default="")
    phone_number = db.Column(db.String(256), nullable=True, default="")
    flutterwave_ref = db.Column(db.String(256), nullable=True)
    status = db.Column(db.String(256), nullable=True)
    tx_ref = db.Column(db.String(256), nullable=True)
    transaction_id = db.Column(db.Integer, nullable=True)
    date_created = db.Column(db.DateTime, default=db.func.current_timestamp())
    transaction_type = db.Column(db.String(256), nullable=True)

