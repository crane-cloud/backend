import jwt

from datetime import datetime, timedelta

from models.organisation import Organisation

from app import db

class Namespace(db.Model):
    """ Namespace table definition """

    _tablename_ = 'namespace'
    # fields of the Namespace table
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256), nullable=False)
    organisation_id = db.Column("organisation_id", db.Integer, db.ForeignKey(Organisation.id))
    date_created = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    def __init__(self, name, organisation_id):
        """ initialize with name and org_id """
        self.name = name
        self.orgainsation_id = organisation_id


    def save(self):
        db.session.add(self)
        db.session.commit()