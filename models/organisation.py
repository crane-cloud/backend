import jwt
from datetime import datetime, timedelta

from app import db

class Organisation(db.Model):
    """ Organisation table definition """

    _tablename_ = 'Organisation'

    # fields of the Organisation table
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256), nullable=False)
    member = db.Column(db.String(256))
    namespace = db.Column(db.String(256))
    date_created = db.Column(db.DateTime, default=db.func.current_timestamp())

    def __init__(self, name, namespace, member):
        """ initialize with name, member and namespace """
        self.name = name
        self.member = member
        self.namespace = namespace


    def save(self):
        db.session.add(self)
        db.session.commit()
