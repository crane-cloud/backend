from sqlalchemy.dialects.postgresql import UUID
from ..models import db
from sqlalchemy import text as sa_text

from app.models.model_mixin import ModelMixin


class BillingMetrics(ModelMixin):
    """ billing metrics table definition """

    __tablename__ = 'billing_metrics'

    # billing metrics fields
    id = db.Column(UUID(as_uuid=True), primary_key=True,
                   server_default=sa_text("uuid_generate_v4()"))
    app_id = db.Column(UUID(as_uuid=True),
                       db.ForeignKey('app.id'), nullable=False)
    invoice_id = db.Column(db.String, db.ForeignKey(
        'billing_invoices.id'), nullable=False)
    memory = db.Column(db.Integer, nullable=True)
    cpu = db.Column(db.Integer, nullable=True)
    network = db.Column(db.Integer, nullable=True)
    storage = db.Column(db.Integer, nullable=True)
