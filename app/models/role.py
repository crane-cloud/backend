from datetime import datetime, timedelta
from sqlalchemy.dialects.postgresql import UUID
from app.models.user import User
from app.models import db
from app.models.model_mixin import ModelMixin

class Role(ModelMixin):
    """  Roles Table Definition """
    _tablename_ = 'role'
    __table_args__ = (db.UniqueConstraint('name', name='org_unique_name'),)

    # fields of the Roles table    
    id = db.Column(UUID(as_uuid=True), unique=True, primary_key=True)
    name = db.Column(db.String(256), nullable=False)

    def __init__(self, name):
        """ initialize with name """
        self.name = name
