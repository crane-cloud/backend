import json
from flask import current_app
from flask_restful import Resource, request
from app.schemas import CreditSchema
from app.models.credits import Credit
from app.helpers.decorators import admin_required
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt_claims

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


class CreditDetailView(Resource):

    @jwt_required
    def get(self, user_id):
        credit_schema = CreditSchema()
        user_credits = Credit.find_first(user_id=user_id)
        user_credits_data, errors = credit_schema.dumps(user_credits)

        if errors:
            return dict(status='fail', message=errors), 400

        return dict(
            status='success',
            data=dict(credit=json.loads(user_credits_data))
        ), 200

