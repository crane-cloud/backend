
from flask_restful import Resource, request
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt_claims
from app.helpers.role_search import has_role

from app.models.transaction_record import TransactionRecord
from app.schemas.transaction_record import TransactionRecordSchema




class TransactionRecordView(Resource):

    @jwt_required
    def post(self):

        current_user_id = get_jwt_identity()
        current_user_roles = get_jwt_claims()['roles']

        transaction_schema = TransactionRecordSchema()
        try:
            transaction_data = request.get_json()

            validated_transaction_data, errors = transaction_schema.load(transaction_data)

            if errors:
                return dict(status='fail', message=errors), 400

            if not has_role(current_user_roles, 'administrator'):
                validated_transaction_data['owner_id'] = current_user_id

            transaction = TransactionRecord(**validated_transaction_data)

            saved = transaction.save()

            if not saved:
                return dict(
                            status='fail',
                            message='An error occured during saving of the record'), 400

            new_transaction_data, errors = transaction_schema.dump(transaction)
            return dict(status='success', data=dict(transaction=new_transaction_data)), 201

        except Exception as err:
            return dict(status='fail', message=str(err)), 500
