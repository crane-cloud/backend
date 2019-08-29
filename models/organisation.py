import jwt

from datetime import datetime, timedelta

from models.user import User

from app import db

association_table = db.Table('association', db.Model,
    db.Column('organisation_id', db.Integer, db.ForeignKey(organisations.id)),
    db.Column('user_id', db.Integer, db.ForeignKey(user.id))
)


class Organisation(db.Model):
    """ Organisation table definition """

    _tablename_ = 'Organisations'

    # fields of the Organisation table
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256), nullable=False)
    namespace = db.Column(db.String(256))
    date_created = db.Column(db.DateTime, default=db.func.current_timestamp())
    member = db.relationship("user", secondary=association_table, backref=db.backref('members', lazy = 'dynamic'))

    def __init__(self, name, namespace, member):
        """ initialize with name, member and namespace """
        self.name = name
        self.member = member
        self.namespace = namespace


    def save(self):
        db.session.add(self)
        db.session.commit()
