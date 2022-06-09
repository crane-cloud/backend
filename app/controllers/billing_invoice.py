from flask import current_app
from flask_restful import Resource, request
from flask_jwt_extended import jwt_required
import sqlalchemy
from app.helpers.cost_modal import get_namespace_cost
from app.helpers.decorators import admin_required
from app.helpers.invoice_notification import send_invoice
from app.models.billing_invoice import BillingInvoice
from app.models.transaction_record import TransactionRecord
from app.models.user import User
from app.models.project import Project
from app.schemas import ProjectSchema, UserSchema
from app.schemas.billing_invoice import BillingInvoiceSchema

class BillingInvoiceView(Resource):
    """
    - Billing Invoice view
    """

    @admin_required
    def post(self, project_id):        
        """
        Required information info:
        - invoice_id, total_amount, project_id(FK), date_cashed
        The post populates the invoice table with metrics data for a project

        """

        billing_invoice_schema = BillingInvoiceSchema()
        project = Project.get_by_id(project_id)
        if not project:
            return dict(
                status='fail',
                message=f'project {project_id} not found'
            ), 404

        user = User.get_by_id(project.owner_id)
        
        if not user:
            return dict(
                status='fail',
                message=f'user {project.owner_id} not found'
            ), 404

        
        existing_invoice = BillingInvoice.query.filter_by(project_id=project_id, is_cashed=False).order_by(
            sqlalchemy.desc(BillingInvoice.date_created)).first()

        if existing_invoice:
            invoice = existing_invoice
        else:
            # Update invoice table
            total_amount = 50000
            # TODO:- Update to use cluster data for cost_data
            # start = project.date_created.timestamp()
            # end = int(datetime.datetime.now().timestamp())
            # window = f'{start},{end}'

            # cost_data = get_namespace_cost(
            #     window, project.alias, series=False, show_deployments=False)
            
            
            #date_cashed # - comes from transaction record
            # date_cashed = TransactionRecord.date_created

            new_invoice_data = dict(
                total_amount=total_amount,
                project_id=project.id,
            )

            validated_invoice_data, errors = billing_invoice_schema.load(
                new_invoice_data
            )

            if errors:
                print('errors', errors)

            invoice = BillingInvoice(**validated_invoice_data)

            invoice.project = project
            saved_invoice = invoice.save()

            if not saved_invoice:
                    return dict(
                                status='fail',
                                message='An error occured during saving of the invoice'), 400


        new_invoice_data, errors = billing_invoice_schema.dump(invoice)

        #Invoice Email details
        sender = current_app.config["MAIL_DEFAULT_SENDER"]
        template = "user/invoice.html"
        subject = "Invoice from Crane Cloud Project"
        email = user.email
        name = user.name
        project_id = project.id
        project_name = project.name
        invoice_date = invoice.date_created
        total_amount = invoice.total_amount

        # send invoice
        send_invoice(
            email,
            name,
            project_id,
            project_name,
            total_amount,
            invoice_date,
            sender,
            current_app._get_current_object(),
            template,
            subject
        )

        return dict(
            status='success',
            message=f'Invoice for user with email {user.email} and project_id {project_id} sent successfully',
            data=dict(invoice=new_invoice_data)
        ), 200
