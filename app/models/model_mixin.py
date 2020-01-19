from sqlalchemy import inspect
from ..models import db


class ModelMixin(db.Model):

    __abstract__ = True

    def save(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def update(self):
        db.session.commit()

    def toDict(self):
        return {
            c.key: getattr(self, c.key) for c in inspect(self).mapper.column_attrs }
