from datetime import datetime, timedelta
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import text as sa_text
from sqlalchemy.orm import relationship, backref
from app.models import billing_invoice, db
from app.models.model_mixin import ModelMixin
from app.models.project_users import ProjectUser
from app.models.anonymous_users import AnonymousUser

class Project(ModelMixin):
    __tablename__ = 'project'
    id = db.Column(UUID(as_uuid=True), primary_key=True, server_default=sa_text("uuid_generate_v4()"))
    name = db.Column(db.String(256), nullable=True)
    alias = db.Column(db.String(256), nullable=False, unique=True)
    owner_id = db.Column(UUID(as_uuid=True), db.ForeignKey('user.id'), nullable=False)
    cluster_id = db.Column(UUID(as_uuid=True), db.ForeignKey('clusters.id'), nullable=False)
    apps = db.relationship('App', backref='project', lazy=True)
    description = db.Column(db.String, nullable=True)
    organisation = db.Column(db.String)
    project_type = db.Column(db.String)
    date_created = db.Column(db.DateTime, default=db.func.current_timestamp())
    users = relationship('ProjectUser', back_populates='other_project')
    project_databases = db.relationship(
        'ProjectDatabase', backref='project', lazy=True)
    project_transactions = db.relationship(
        'TransactionRecord', backref='project', lazy=True)
    billing_invoices = db.relationship(
        'BillingInvoice', backref='project', lazy=True)
    anonymoususers = db.relationship('AnonymousUser', backref='anonymous_project_users', lazy=True)
