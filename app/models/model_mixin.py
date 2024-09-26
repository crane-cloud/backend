from sqlalchemy import inspect, func, column
from sqlalchemy.exc import SQLAlchemyError
from flask_sqlalchemy import BaseQuery
from ..models import db
from sqlalchemy import or_
import time
from types import SimpleNamespace


class SoftDeleteQuery(BaseQuery):
    def __new__(cls, *args, **kwargs):
        obj = super(SoftDeleteQuery, cls).__new__(cls)
        with_deleted = kwargs.pop('_with_deleted', False)
        if len(args) > 0:
            super(SoftDeleteQuery, obj).__init__(*args, **kwargs)
            entities = obj._entities
            filtered_entities = [
                entity for entity in entities if hasattr(entity, 'deleted')]
            if not with_deleted:
                deleted_column = getattr(
                    obj._entities[0].mapper.class_, 'deleted')
                return obj.filter(*filtered_entities).filter(
                    or_(deleted_column == False, deleted_column == None))
        return obj

    def __init__(self, *args, **kwargs):
        super(SoftDeleteQuery, self).__init__(*args, **kwargs)

    def with_deleted(self):
        return self.__class__(self._only_full_mapper_zero('get'),
                              session=db.session(), _with_deleted=True)


class ModelMixin(db.Model):

    __abstract__ = True

    def save(self):
        try:
            db.session.add(self)
            db.session.commit()
            return True
        except SQLAlchemyError:
            db.session.rollback()
            return False

    def delete(self):
        try:
            db.session.delete(self)
            db.session.commit()
            return True
        except SQLAlchemyError:
            db.session.rollback()
            return False

    def soft_delete(self):
        try:
            setattr(self, 'deleted', True)
            setattr(self, 'name', f"{self.name}_deleted_{int(time.time())}")
            db.session.commit()
            return True
        except SQLAlchemyError:
            db.session.rollback()
            return False

    @classmethod
    def bulk_save(cls, objects):
        try:
            db.session.bulk_save_objects(objects)
            db.session.commit()
            return True
        except SQLAlchemyError:
            db.session.rollback()
            return False

    @classmethod
    def update(cls, instance, **kwargs):
        try:
            if instance is None:
                return False

            for key, value in kwargs.items():
                setattr(instance, key, value)
            db.session.commit()
            return True
        except SQLAlchemyError:
            db.session.rollback()
            return False

    @classmethod
    def find_first(cls, **kwargs):
        try:
            return cls.query.filter_by(**kwargs).first()
        except SQLAlchemyError:
            return False

    @classmethod
    def find_all(cls, **kwargs):
        paginate = kwargs.pop('paginate', False)
        page = kwargs.pop('page', 1)
        per_page = kwargs.pop('per_page', 10)

        try:
            if paginate:
                result = cls.query.filter_by(
                    **kwargs).order_by(cls.date_created.desc()).paginate(page=page, per_page=per_page, error_out=False)
                pagination = {
                    'total': result.total,
                    'pages': result.pages,
                    'page': result.page,
                    'per_page': result.per_page,
                    'next': result.next_num,
                    'prev': result.prev_num,
                }
                return SimpleNamespace(
                    pagination=pagination,
                    items=result.items)
            else:
                return cls.query.filter_by(**kwargs).all()
        except SQLAlchemyError:
            return False

    @classmethod
    def count(cls, **kwargs):
        return cls.query.filter_by(**kwargs).count()

    @classmethod
    def check_exists(cls, **kwargs):
        result = cls.query.filter_by(**kwargs).count()

        if result > 0:
            return True
        return False

    @classmethod
    def get_by_id(cls, id):
        try:
            return cls.query.filter_by(id=id).first()
        except SQLAlchemyError as e:
            return False

    def toDict(self):
        return {
            c.key: getattr(self, c.key) for c in inspect(self).mapper.column_attrs}

    @classmethod
    def graph_data(cls, start, end, set_by):
        if set_by == 'month':
            date_list = func.generate_series(
                start, end, '1 month').alias('month')
            month = column('month')

            app_data = db.session.query(month, func.count(cls.id)).\
                select_from(date_list).\
                outerjoin(cls, func.date_trunc('month', cls.date_created) == month).\
                group_by(month).\
                order_by(month).\
                all()

        else:
            date_list = func.generate_series(
                start, end, '1 year').alias('year')
            year = column('year')

            app_data = db.session.query(year, func.count(cls.id)).\
                select_from(date_list).\
                outerjoin(cls, func.date_trunc('year', cls.date_created) == year).\
                group_by(year).\
                order_by(year).\
                all()

        app_info = []
        for item in app_data:
            item_dict = {
                'year': item[0].year, 'month': item[0].month, 'value': item[1]
            }
            app_info.append(item_dict)
        return app_info
