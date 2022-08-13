from sqlalchemy.dialects.postgresql import UUID
from ..models import db
from sqlalchemy import text as sa_text
from app.models.model_mixin import ModelMixin


class UserPaymentDetails(ModelMixin):
    """ user payment model definition """

    __tablename__ = 'user_payment_details'

    # user payment details fields
    id = db.Column(UUID(as_uuid=True), primary_key=True,
                    server_default=sa_text("uuid_generate_v4()"))
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('user.id'), nullable=False)
    card_number = db.Column(db.Integer, nullable=True)
    card_expiry = db.Column(db.Date)
    mobile_money_number = db.Column(db.String)

    