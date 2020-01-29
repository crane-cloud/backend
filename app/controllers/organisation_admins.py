import json
from flask import current_app
from flask_restful import Resource, request
from app.schemas import OrganisationSchema
from app.schemas import OrgAdminSchema
from app.schemas import UserSchema
from app.models.organisation_admins import OrganisationAdmins
from app.models.user import User
from app.models.organisation import Organisation


class OrgAdminView(Resource):

    def post(self):
        """
        """

        org_admin_schema = OrgAdminSchema()

        org_admin_data = request.get_json()

        validated_org_admin_data, errors = org_admin_schema.load(org_admin_data)

        if errors:
            return dict(status='fail', message=errors), 400

        org_admin = OrganisationAdmins(**validated_org_admin_data)

        saved_org_admin = org_admin.save()

        if not saved_org_admin:
            return dict(status='fail', message='Internal Server Error'), 500

        new_org_admin_data, errors = org_admin_schema.dumps(org_admin)

        return dict(status='success', data=dict(organisation_admin=json.loads(new_org_admin_data))), 201

    def get(self):
        """
        """
        org_admin_schema = OrgAdminSchema(many=True)

        org_admin = OrganisationAdmins.find_all()

        org_admin_data, errors = org_admin_schema.dumps(org_admin)

        if errors:
            return dict(status="fail", message="Internal Server Error"), 500

        return dict(status="success", data=dict(organisation_admin=json.loads(org_admin_data))), 200


class OrgAdminDetailView(Resource):

    """ Get Admins in an Organisation """
    def get(self, organisation_id):
        organisation_schema = OrganisationSchema(many=True)
        
        admins = self.getOrgAdmins(organisation_id)
        
        if not admins:
            return dict(status="fail", message="Organisation doesnt Exist"), 404

        admins_data, errors = organisation_schema.dumps(admins)

        if errors:
            return dict(status="fail", message="Internal Server Error"), 500

        return dict(status="success", data=dict(admins=json.loads(admins_data))), 200


    def getOrgAdmins(self, organisation_id):
        organisation = Organisation.find_first(id=organisation_id)
        if not organisation:
            return False
        return organisation.admins

