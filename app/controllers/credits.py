import json
from flask_restful import Resource
from app.schemas import CreditSchema
from marshmallow import ValidationError
from app.models.credits import Credit
from app.helpers.decorators import admin_required
from flask_jwt_extended import jwt_required

class CreditView(Resource):

    @admin_required
    def get(self):

        credit_schema = CreditSchema(many=True)

        users_credit = Credit.find_all()

        try:
            users_credit_data = credit_schema.dumps(users_credit)
        except ValidationError as err:
            return dict(status="fail", message=err.message), 400

        return dict(
            status='success',
            data=dict(credit=json.loads(users_credit_data))
        ), 200


class CreditDetailView(Resource):

    @jwt_required()
    def get(self, user_id):
        credit_schema = CreditSchema()
        user_credits = Credit.find_first(user_id=user_id)

        try:
            user_credits_data = credit_schema.dumps(user_credits)
        except ValidationError as err:
            return dict(status="fail", message=err.message), 400

        return dict(
            status='success',
            data=dict(credit=json.loads(user_credits_data))
        ), 200

