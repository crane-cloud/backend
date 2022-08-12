import datetime
from flask_restful import Resource, request
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt_claims
import sqlalchemy
from app.helpers.admin import is_owner_or_admin
from app.helpers.role_search import has_role
import json
from app.models import billing_invoice
from app.models.billing_invoice import BillingInvoice
from app.models.project import Project
from app.models.user import User
from app.models.credits import Credit
from app.models.transaction_record import TransactionRecord
from app.schemas.transaction_record import TransactionRecordSchema
from app.helpers.secret_generator import generate_transaction_id



class TransactionRecordView(Resource):

    @jwt_required
    def post(self, project_id):

        current_user_id = get_jwt_identity()
        current_user_roles = get_jwt_claims()['roles']

        transaction_schema = TransactionRecordSchema()

        project = Project.get_by_id(project_id)
        if not project:
            return dict(status='fail', message=f'project {project_id} not found'), 404
        
        if not is_owner_or_admin(project, current_user_id, current_user_roles):
            return dict(status='fail', message='Unauthorised'), 403



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
            transaction_type = validated_transaction_data['transaction_type']
            # comments for implementation flow
            # get the latest invoice for a project by date
            invoice = BillingInvoice.query.filter_by(project_id=project_id, is_cashed=False).order_by(
                sqlalchemy.desc(BillingInvoice.date_created)).first()

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
                tx_ref=tx_ref,
                transaction_type=transaction_type
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
            

            transaction = TransactionRecord(**validated_transaction_data)

            transaction.invoice = invoice
            transaction.billing_invoice_id = invoice.id
            transaction.invoice.is_cashed = True
            transaction.invoice.date_cashed = datetime.datetime.now()

            saved_transaction = transaction.save()

            if not saved_transaction:
                return dict(
                            status='fail',
                            message='An error occured during saving of the record'), 400

            # Creating new invoice
            new_invoice = BillingInvoice(project_id=project_id)

            saved_new_invoice = new_invoice.save()

            if not saved_new_invoice:
                return dict(
                            status='fail',
                            message='An error occured during updating of new invoice record'), 400

            new_transaction_data, errors = transaction_schema.dump(transaction)
            return dict(status='success', data=dict(
                        transaction={**new_transaction_data, 
                        "billing_invoice_id":str(transaction.billing_invoice_id)})), 201

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



    @jwt_required
    def patch(self,project_id ,record_id):

        current_user_id = get_jwt_identity()
        current_user_roles = get_jwt_claims()['roles']

        update_data = request.get_json()

        transaction_schema = TransactionRecordSchema(partial=True)
        validated_transaction_data, errors = transaction_schema.load(update_data)
        
        if errors:
            return dict(status="fail", message=errors), 400

        project = Project.get_by_id(project_id)

        if not is_owner_or_admin(project, current_user_id, current_user_roles):
                return dict(status='fail', message='Unauthorised'), 403

        transaction = TransactionRecord.get_by_id(record_id)

        if not transaction:
            return dict(
                status='fail',
                message=f'transaction with record {record_id} not found'
            ), 404

        if 'status' in validated_transaction_data:
            transaction.status = validated_transaction_data['status']

        updated_transaction = transaction.save()

        if not updated_transaction:
            return dict(status='fail', message='Internal Server Error'), 500

        return dict(
            status="success",
            message=f"Transaction {transaction.id} updated successfully"
        ), 200

class CreditTransactionRecordView(Resource):
    
    @jwt_required
    def post(self, project_id):

        current_user_id = get_jwt_identity()
        current_user_roles = get_jwt_claims()['roles']

        transaction_schema = TransactionRecordSchema()

        try:
            transaction_data = request.get_json()

            validated_transaction_data, errors = transaction_schema.load(
                transaction_data, partial=True)

            if errors:
                return dict(status='fail', message=errors), 400

            amount = validated_transaction_data['amount']
            
            # check if owner has enough credits
            project = Project.get_by_id(project_id)
            if not project:
                return dict(status='fail', message=f'project {project_id} not found'), 404
            
            owner_id=project.owner_id
            user_credit = Credit.find_first(user_id=owner_id)
            user_credit_amount = user_credit.amount

            
            if amount > user_credit_amount:
                return dict(status='fail', message='not enough credits'), 400

            user_credit.amount = user_credit.amount - amount
            updated_user_credit = user_credit.save()

            if not updated_user_credit:
                return dict(status='fail', message='Internal Server Error'), 500

            
            # comments for implementation flow
            # get the latest invoice for a project by date
            invoice = BillingInvoice.query.filter_by(project_id=project_id, is_cashed=False).order_by(
                sqlalchemy.desc(BillingInvoice.date_created)).first()


            
            user = User.get_by_id(owner_id)
            transaction_id = generate_transaction_id()

            new_transaction_record_info = dict(
                owner_id=str(project.owner_id),
                amount=amount,
                currency='USD',
                email=user.email,
                project_id=project_id,
                name=user.name,
                status='success',
                transaction_id=transaction_id,
                transaction_type='credits'
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
            
            transaction.invoice = invoice
            transaction.billing_invoice_id = invoice.id
            transaction.invoice.is_cashed = True
            transaction.invoice.date_cashed = datetime.datetime.now()
            
            saved_transaction = transaction.save()

            if not saved_transaction:
                return dict(
                            status='fail',
                            message='An error occured during saving of the record'), 400
            
            new_invoice = BillingInvoice(project_id=project_id)

            saved_new_invoice = new_invoice.save()

            if not saved_new_invoice:
                return dict(
                            status='fail',
                            message='An error occured during updating of new invoice record'), 400

            new_invoice = BillingInvoice(project_id=project_id)

            saved_new_invoice = new_invoice.save()

            if not saved_new_invoice:
                return dict(
                            status='fail',
                            message='An error occured during updating of new invoice record'), 400

            new_transaction_data, errors = transaction_schema.dump(transaction)
            return dict(status='success', data=dict(
                        transaction={**new_transaction_data, 
                        "billing_invoice_id":str(transaction.billing_invoice_id)})), 201

        except Exception as err:
            return dict(status='fail', message=str(err)), 500

        
