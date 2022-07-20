import json
from flask import current_app
from flask_restful import Resource, request
from app.schemas import CreditSchema
from app.models.credits import Credit
from app.helpers.decorators import admin_required


class CreditView(Resource):

    @admin_required
    def get(self):

        credit_schema = CreditSchema(many=True)

        users_credit = Credit.find_all()

        users_credit_data, errors = credit_schema.dumps(users_credit)

        if errors:
            return dict(status='fail', message=errors), 400

        return dict(
            status='success',
            data=dict(credit=json.loads(users_credit_data))
        ), 200