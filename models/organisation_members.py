from app import db
from models.user import User
from models.organisation import Organisation
from sqlalchemy import inspect

from helpers.toDict import ToDict

class OrganisationMembers(db.Model, ToDict):

    _tablename_ = "organisation_members"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column('user_id', db.Integer, db.ForeignKey(User.id, ondelete='CASCADE'), nullable=False)
    organisation_id = db.Column("organisation_id", db.Integer, db.ForeignKey(Organisation.id, ondelete='CASCADE'), nullable=False)
    
    def __init__(self, user_id, organisation_id):
        """ initialize with name, member and namespace """  
        self.user_id = user_id
        self.organisation_id = organisation_id


    def save(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

