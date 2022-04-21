import pdb
from flask_restful import Resource, request
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt_claims
from app.helpers.admin import is_owner_or_admin
from app.helpers.role_search import has_role
import json
from app.models.project import Project

from app.models.transaction_record import TransactionRecord
from app.schemas.transaction_record import TransactionRecordSchema




class TransactionRecordView(Resource):

    @jwt_required
    def post(self, project_id):

        current_user_id = get_jwt_identity()
        current_user_roles = get_jwt_claims()['roles']

        transaction_schema = TransactionRecordSchema()

        try:
            transaction_data = request.get_json()

            validated_transaction_data, errors = transaction_schema.load(
                transaction_data, partial=("project_id"))

            if errors:
                return dict(status='fail', message=errors), 400

            amount = validated_transaction_data['amount']
            currency = validated_transaction_data['currency']
            email = validated_transaction_data['email']
            flutterwave_ref = validated_transaction_data['flutterwave_ref']
            name = validated_transaction_data['name']
            phone_number = validated_transaction_data['phone_number']
            status = validated_transaction_data['status']
            transaction_id = validated_transaction_data['transaction_id']
            tx_ref = validated_transaction_data['tx_ref']

            project = Project.get_by_id(project_id)
            if not project:
                return dict(status='fail', message=f'project {project_id} not found'), 404

            new_transaction_record_info = dict(
                owner_id=str(project.owner_id),
                amount=amount,
                currency=currency,
                phone_number=phone_number,
                email=email,
                flutterwave_ref=flutterwave_ref,
                project_id=project_id,
                name=name,
                status=status,
                transaction_id=transaction_id,
                tx_ref=tx_ref
            )
            
            validated_transaction_data, errors = transaction_schema.load(
            new_transaction_record_info)

            validated_transaction_data['project_id'] = project_id

            transaction_record_existent = TransactionRecord.find_first(
                transaction_id=transaction_id
            )

            if transaction_record_existent:
                return dict(
                status="fail",
                message=f"Transaction with id {transaction_id} Already Exists."
                ), 400
            
            if not is_owner_or_admin(project, current_user_id, current_user_roles):
                return dict(status='fail', message='Unauthorised'), 403

            transaction = TransactionRecord(**validated_transaction_data)

            saved_transaction = transaction.save()

            if not saved_transaction:
                return dict(
                            status='fail',
                            message='An error occured during saving of the record'), 400

            new_transaction_data, errors = transaction_schema.dump(transaction)
            return dict(status='success', data=dict(transaction=new_transaction_data)), 201

        except Exception as err:
            return dict(status='fail', message=str(err)), 500

    
    @jwt_required
    def get(self, project_id):

        current_user_id = get_jwt_identity()
        current_user_roles = get_jwt_claims()['roles']

        transaction_schema = TransactionRecordSchema(many=True)
        project = Project.get_by_id(project_id)

        transaction = TransactionRecord.find_all(project_id=project_id)

        if not transaction:
            return dict(
                status='fail',
                message=f'transaction records not found'
            ), 404
        
        
        if not is_owner_or_admin(project, current_user_id, current_user_roles):
                return dict(status='fail', message='Unauthorised'), 403

        transaction_data, errors = transaction_schema.dumps(transaction)

        if errors:
            return dict(status='fail', message=errors), 500

        return dict(status='success', data=dict(
            transaction=json.loads(transaction_data))), 200


class TransactionRecordDetailView(Resource):
    
    @jwt_required
    def get(self,project_id ,record_id):

        current_user_id = get_jwt_identity()
        current_user_roles = get_jwt_claims()['roles']

        transaction_schema = TransactionRecordSchema()
        project = Project.get_by_id(project_id)

        transaction = TransactionRecord.get_by_id(record_id)

        if not transaction:
            return dict(
                status='fail',
                message=f'transaction with record {record_id} not found'
            ), 404

        if not is_owner_or_admin(project, current_user_id, current_user_roles):
                return dict(status='fail', message='Unauthorised'), 403

        transaction_data, errors = transaction_schema.dumps(transaction)
        
        if errors:
            return dict(status='fail', message=errors), 500

        return dict(status='success', data=dict(
            transaction=json.loads(transaction_data))), 200
