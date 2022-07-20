import json
from flask import current_app
from flask_restful import Resource, request
from app.schemas import CreditAssignmentSchema
from app.models.credit_assignments import CreditAssignment
from app.models.credits import Credit
from app.helpers.decorators import admin_required


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
