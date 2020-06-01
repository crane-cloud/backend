from sqlalchemy import inspect
class ToDict():
    def toDict(self):
        return { c.key: getattr(self, c.key) for c in inspect(self).mapper.column_attrs}