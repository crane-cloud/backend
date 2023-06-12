from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import text as sa_text
from app.models import db
from app.models.model_mixin import ModelMixin, SoftDeleteQuery
from flask_bcrypt import Bcrypt


class ProjectDatabase(ModelMixin):
    __tablename__ = 'project_database'
    # SoftDeleteQuery is used to filter out deleted records
    query_class = SoftDeleteQuery

    id = db.Column(UUID(as_uuid=True), primary_key=True,
                   server_default=sa_text("uuid_generate_v4()"))
    host = db.Column(db.String(256), nullable=True)
    name = db.Column(db.String(256), nullable=False)
    user = db.Column(db.String(256), nullable=False)
    password = db.Column(db.String(256), nullable=False)
    project_id = db.Column(UUID(as_uuid=True), db.ForeignKey(
        'project.id'))
    date_created = db.Column(db.DateTime, default=db.func.current_timestamp())
    port = db.Column(db.Integer, nullable=True)
    database_flavour_name = db.Column(db.String(256))
    deleted = db.Column(db.Boolean, default=False)
    disabled = db.Column(db.Boolean, default=False)
    # TODO: make database_flavour_name nullable=false

    def password_is_valid(self, password):
        """ checks the password against it's hash to validate the user's password """
        return Bcrypt().check_password_hash(self.password, password)
