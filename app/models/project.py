from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import text as sa_text
from sqlalchemy.orm import relationship
from app.models import db
from app.models.model_mixin import ModelMixin, SoftDeleteQuery
from app.models.project_users import ProjectFollowers


class Project(ModelMixin):
    __tablename__ = 'project'
    # SoftDeleteQuery is used to filter out deleted records
    query_class = SoftDeleteQuery

    id = db.Column(UUID(as_uuid=True), primary_key=True,
                   server_default=sa_text("uuid_generate_v4()"))
    name = db.Column(db.String(256), nullable=True)
    alias = db.Column(db.String(256), nullable=False, unique=True)
    owner_id = db.Column(UUID(as_uuid=True),
                         db.ForeignKey('user.id'), nullable=False)
    cluster_id = db.Column(UUID(as_uuid=True), db.ForeignKey(
        'clusters.id'), nullable=False)
    apps = db.relationship('App', backref='project', lazy=True)
    description = db.Column(db.String, nullable=True)
    organisation = db.Column(db.String)
    project_type = db.Column(db.String)
    date_created = db.Column(db.DateTime, default=db.func.current_timestamp())
    users = relationship('ProjectUser', back_populates='other_project')
    followers = relationship('ProjectFollowers', back_populates='project')
    is_public = db.Column(db.Boolean, default=True)
    project_transactions = db.relationship(
        'TransactionRecord', backref='project', lazy=True)
    billing_invoices = db.relationship(
        'BillingInvoice', backref='project', lazy=True)
    anonymoususers = db.relationship(
        'AnonymousUser', backref='anonymous_project_users', lazy=True)
    deleted = db.Column(db.Boolean, default=False)
    disabled = db.Column(db.Boolean, default=False)
    admin_disabled = db.Column(db.Boolean, default=False)
    tags = relationship('ProjectTag', back_populates='project')

    def is_followed_by(self, user):
        return any(follower.user_id == user.id for follower in self.followers)

