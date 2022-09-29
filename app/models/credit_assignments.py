from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import text as sa_text
from app.models import db
from app.models.model_mixin import ModelMixin
from datetime import datetime, date, timedelta
from dateutil.relativedelta import *

class CreditAssignment(ModelMixin):
    __tablename__ = 'credit_assignments'
    id = db.Column(UUID(as_uuid=True), primary_key=True, server_default=sa_text("uuid_generate_v4()"))
    amount = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String, nullable=True)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('user.id'), nullable=False)
    date_created = db.Column(db.DateTime, default=db.func.current_timestamp())
    expiry_date = db.Column(db.DateTime)


    def __init__(self,user_id, amount,description, expiry_date=None):
        self.user_id = user_id
        self.amount = amount
        self.description = description
        self.expiry_date = expiry_date if expiry_date else datetime.utcnow() +relativedelta(months=+6)