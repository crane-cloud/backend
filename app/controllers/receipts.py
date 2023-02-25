

import json
from flask_restful import Resource, request
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt_claims
from app.helpers.admin import is_owner_or_admin
from app.models.project import Project
from app.models.transaction_record import TransactionRecord
from app.schemas.billing_receipts import BillingReceiptSchema


class BillingReceiptsView(Resource):
    """
    - Billing receipts view
    """

    @jwt_required
    def get(self, project_id):

        current_user_id = get_jwt_identity()
        current_user_roles = get_jwt_claims()['roles']

        page = request.args.get('page', 1,type=int)
        per_page = request.args.get('per_page', 10, type=int)

        billing_receipt_schema = BillingReceiptSchema(many=True)
        project = Project.get_by_id(project_id)

        if not project:
            return dict(status='fail', message='Project with project id {project_id} not found'), 404

        
        if not is_owner_or_admin(project, current_user_id, current_user_roles):
                return dict(status='fail', message='Unauthorised'), 403

        billing_receipts = TransactionRecord.find_all(project_id=project_id, paginate=True, page=page, per_page=per_page)

        if not billing_receipts:
            return dict(
                status='fail',
                message=f'billing receipt records not found'
            ), 404

        billing_receipts_data, errors = billing_receipt_schema.dumps(billing_receipts.items)

        if errors:
            return dict(status='fail', message=errors), 500

        return dict(status='success', data=dict(
            billing_receipts=json.loads(billing_receipts_data) , pagination=billing_receipts.pagination)), 200


class BillingReceiptsDetailView(Resource):

    @jwt_required
    def get(self, project_id ,receipt_id):

        current_user_id = get_jwt_identity()
        current_user_roles = get_jwt_claims()['roles']

        billing_invoice_schema = BillingReceiptSchema()
        project = Project.get_by_id(project_id)

        if not project:
            return dict(status='fail', message='Project with project id not found'), 404

        if not is_owner_or_admin(project, current_user_id, current_user_roles):
                return dict(status='fail', message='Unauthorised'), 403

        billing_receipt = TransactionRecord.get_by_id(receipt_id)

        if not billing_receipt:
            return dict(
                status='fail',
                message=f'billing receipt with invoice id {receipt_id} not found'
            ), 404

        billing_receipt_data, errors = billing_invoice_schema.dumps(billing_receipt)
        
        if errors:
            return dict(status='fail', message=errors), 500

        return dict(status='success', data=dict(
            billing_receipt=json.loads(billing_receipt_data))), 200
