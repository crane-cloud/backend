from flask_restful import Resource, request
from flask_jwt_extended import jwt_required



class BillingInvoiceView(Resource):
    """
    - Billing Invoice view
    """

    @jwt_required
    def post(self, project_id):
        ...
    """
    Required information info:
    - invoice_id, total_amount, project_id(FK), date_cashed
    The post populates the invoice table with metrics data for a project

    """