import json
from flask import current_app
from flask_restful import Resource, request
from app.schemas import CreditAssignmentSchema
from app.models.credit_assignments import CreditAssignment
from app.helpers.admin import is_owner_or_admin, is_current_or_admin
from app.models.credits import Credit
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt_claims
from app.helpers.decorators import admin_required
from app.models.user import User


class CreditAssignmentView(Resource):

    # assign credits to user
    @admin_required
    def post(self):
        """
        """

        credit_assignment_schema = CreditAssignmentSchema()

        credit_assignment_data = request.get_json()

        validated_credit_assignment_data, errors = credit_assignment_schema.load(credit_assignment_data)

        user_id = validated_credit_assignment_data.get('user_id', None)
        amount = validated_credit_assignment_data.get('amount', None)

        if errors:
            return dict(status="fail", message=errors), 400

        user_id_existant = Credit.find_first(user_id=user_id)

        # check if user has already been assigned credits

        if user_id_existant:
            if 'amount' in validated_credit_assignment_data:
                user_id_existant.amount = user_id_existant.amount + validated_credit_assignment_data['amount']

            updated_user_id_existant = user_id_existant.save()

            if not updated_user_id_existant:
                return dict(status='fail', message='Internal Server Error'), 500


            credit_assignment = CreditAssignment(**validated_credit_assignment_data)
            saved_credit_assignment = credit_assignment.save()

            if not saved_credit_assignment:
                return dict(status='fail', message=f'Internal Server Error'), 500

            return dict(
                status="success",
                message=f"Credit for user_id {credit_assignment.user_id} allocated successfully"
            ), 201

        # if user has not been assigned credits
        
        credit = Credit(user_id = user_id, amount = amount)
        saved_credit = credit.save()

        if not saved_credit:
            return dict(status='fail', message=f'Internal Server Error'), 500

        credit_assignment = CreditAssignment(**validated_credit_assignment_data)
        saved_credit_assignment = credit_assignment.save()

        if not saved_credit_assignment:
            return dict(status='fail', message=f'Internal Server Error'), 500

        return dict(
            status="success",
            message=f"Credit for user_id {credit_assignment.user_id} allocated successfully"
        ), 201

class CreditAssignmentDetailView(Resource):

    # get single user user credit assignment records
    @jwt_required
    def get(self, user_id):
        """
        """
        current_user_id = get_jwt_identity()
        current_user_roles = get_jwt_claims()['roles']

        if not is_current_or_admin(user_id, current_user_id, current_user_roles):
            return dict(status='fail', message='unauthorised'), 403

        credit_assignment_schema = CreditAssignmentSchema(many = True)

        user = User.get_by_id(user_id)

        if not user:
            return dict(status='fail', message=f'user {user_id} not found'), 404

        credit_assignment_records = user.credit_assignments
        

        credit_assignments_json, errors = credit_assignment_schema.dumps(credit_assignment_records)

        if errors:
            return dict(status='fail', message='Internal server error'), 500

        return dict(
            status='success',
            data=dict(credit_assignment_records=json.loads(credit_assignments_json))
        ), 200