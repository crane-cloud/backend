from datetime import datetime, timedelta
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, backref
from app.models.user import User
from app.models import db
from app.models.model_mixin import ModelMixin

class Role(ModelMixin):
    """  Roles Table Definition """
    _tablename_ = 'role'

    # fields of the Roles table  
    id = db.Column(db.Integer, primary_key=True)  
    name = db.Column(db.String(256), nullable=False)

    users = relationship('User', secondary='user_role', backref='roles')


    def __init__(self, name):
        """ initialize with name """
        self.name = name
