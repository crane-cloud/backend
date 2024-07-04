from sqlalchemy.dialects.postgresql import UUID
from app.models import db
from app.models.model_mixin import ModelMixin, SoftDeleteQuery
from sqlalchemy import text as sa_text


class Tag(ModelMixin):
    __tablename__ = "tag"
    query_class = SoftDeleteQuery

    id = db.Column(UUID(as_uuid=True), primary_key=True,
                   server_default=sa_text("uuid_generate_v4()"))
    name = db.Column(db.String)
    deleted = db.Column(db.Boolean, default=False)
    date_created = db.Column(db.DateTime, default=db.func.current_timestamp())
