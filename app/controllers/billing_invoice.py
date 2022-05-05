import os
from flask import current_app
from flask_restful import Resource, request
from flask_jwt_extended import jwt_required
from app.helpers.decorators import admin_required
from app.helpers.invoice_notification import send_invoice
from app.models.user import User
from app.models.project import Project
from app.schemas import ProjectSchema, UserSchema

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
       
        #Invoice Email details
        sender = current_app.config["MAIL_DEFAULT_SENDER"]
        template = "templates/invoice.html"
        subject = "Invoice from Crane Cloud Project"
        email = user.email
        name = user.name
        # send verification
        send_invoice(
            email,
            name,
            sender,
            current_app._get_current_object(),
            template,
            subject
        )
        #To do: Add other parameters dynamically i.e Project ID, Total due, Balance due

        return dict(
            status='success',
            message=f'Invoice for user {user.id} and project {project_id} sent successfully'
        ), 200