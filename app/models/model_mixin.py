from sqlalchemy import inspect, func, column
from sqlalchemy.exc import SQLAlchemyError
from ..models import db

class ModelMixin(db.Model):

    __abstract__ = True

    def save(self):
        try:
            db.session.add(self)
            db.session.commit()
            return True
        except SQLAlchemyError as e:
            print(e)
            db.session.rollback()
            return False

    def delete(self):
        try:
            db.session.delete(self)
            db.session.commit()
            return True
        except SQLAlchemyError as e:
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
        except SQLAlchemyError as e:
            db.session.rollback()
            return False

    @classmethod
    def find_first(cls, **kwargs):
        try:
            return cls.query.filter_by(**kwargs).first()
        except SQLAlchemyError as e:
            return False

    @classmethod
    def find_all(cls, **kwargs):
        try:
            return cls.query.filter_by(**kwargs).all()
        except SQLAlchemyError as e:
            return False

    @classmethod
    def count(cls, **kwargs):
        return cls.query.filter_by(**kwargs).count()

    @classmethod
    def check_exists(cls, **kwargs):
        result = cls.query.filter_by(**kwargs).count()

        if result > 0:
            return False
        return False

    @classmethod
    def get_by_id(cls, id):
        try:
            return cls.query.get(id)
        except SQLAlchemyError:
            return False

    def toDict(self):
        return {
            c.key: getattr(self, c.key) for c in inspect(self).mapper.column_attrs}


    def graph_data(self, start, end, set_by):
        if set_by == 'month':
            date_list = func.generate_series(
                start, end, '1 month').alias('month')
            month = column('month')

            app_data = db.session.query(month, func.count(self.id)).\
                select_from(date_list).\
                outerjoin(self, func.date_trunc('month', self.date_created) == month).\
                group_by(month).\
                order_by(month).\
                all()

        else:
            date_list = func.generate_series(
                start, end, '1 year').alias('year')
            year = column('year')

            app_data = db.session.query(year, func.count(self.id)).\
                select_from(date_list).\
                outerjoin(self, func.date_trunc('year', self.date_created) == year).\
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
