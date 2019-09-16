import jwt

from datetime import datetime, timedelta

from models.user import User

from app import db

from helpers.toDict import ToDict

class Organisation(db.Model, ToDict):
    """ Organisation table definition """

    _tablename_ = 'organisations'
    # fields of the Organisation table
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256), nullable=False)
    date_created = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    def __init__(self, name):
        """ initialize with name, member and namespace """
        self.name = name


    def save(self):
        db.session.add(self)
        db.session.commit()
