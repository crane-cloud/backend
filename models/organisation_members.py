from app import db
from models.user import User
from models.organisation import Organisation

from sqlalchemy import inspect

from helpers.toDict import ToDict

from marshmallow import Schema, fields

class OrganisationMembers(db.Model, ToDict):

    _tablename_ = "organisation_members"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column('user_id', db.Integer, db.ForeignKey(User.id))
    organisation_id = db.Column("organisation_id", db.Integer, db.ForeignKey(Organisation.id))

    def __init__(self, user_id, organisation_id):
        """ initialize with name, member and namespace """
        self.user_id = user_id
        self.organisation_id = organisation_id


    def save(self):
        db.session.add(self)
        db.session.commit()

class OrganisationMemberSchema(Schema):
    id = fields.Int(dump_only=True)
    organisation_id = fields.Int()
    user_id = fields.Int()
    