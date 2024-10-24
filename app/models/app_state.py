from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import text as sa_text
from app.models import db
from app.models.model_mixin import ModelMixin
import enum


class AppStatusList(enum.Enum):
    running = "running"
    unknown = "unknown"
    failed = "failed"
    down = "down"

    def __str__(self):
        return self.value  


class AppState(ModelMixin):
    __tablename__ = 'app_state'
    id = db.Column(UUID(as_uuid=True), primary_key=True,
                   server_default=sa_text("uuid_generate_v4()"))
    app = db.Column(UUID(as_uuid=True), db.ForeignKey(
        'app.id'), nullable=False)
    failure_reason = db.Column(db.String)
    message = db.Column(db.String)
    status = db.Column(db.Enum(AppStatusList), nullable=False)
    last_check = db.Column(db.DateTime, default=db.func.current_timestamp())
