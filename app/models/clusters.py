import os
from sqlalchemy_utils import EncryptedType
from flask import current_app as app
from app.models import db
from app.models.model_mixin import ModelMixin

secret = os.getenv('FLASK_APP_SECRET')


class Cluster(ModelMixin):

    __tablename__ = 'clusters'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String, nullable=False, unique=True)
    host = db.Column(db.String, nullable=False, unique=True)
    token = db.Column(EncryptedType(db.String, secret), nullable=False)
