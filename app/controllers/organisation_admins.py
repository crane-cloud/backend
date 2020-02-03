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

    def post(self, organisation_id):
        """
        """

        org_admin_schema = OrgAdminSchema()

        org_admin_data = request.get_json()

        validated_org_admin_data, errors = org_admin_schema.load(org_admin_data)

        if errors:
            return dict(status='fail', message=errors), 400


        # Get User
        user = User.get_by_id(validated_org_admin_data.get('user_id', None))
        
        if not user:
            return dict(status='fail', message='User not found'), 404

        # Get organisation
        organisation = Organisation.get_by_id(organisation_id)

        if not organisation:
            return dict(status='fail', message='Organisation not found'), 404

        if user in organisation.admins:
            return dict(status='fail', message='Admin already exist'), 409

        # adding user to organisation admins
        organisation.admins.append(user)

        saved_org_admin = organisation.save()

        user_schema = UserSchema()

        if not saved_org_admin:
            return dict(status='fail', message='Internal Server Error'), 500

        new_org_admin_data, errors = user_schema.dumps(user)

        return dict(status='success', data=dict(organisation_admin=json.loads(new_org_admin_data))), 201


    def get(self, organisation_id):
        """
        """
        org_schema = OrganisationSchema(many=True)

        organisation = Organisation.get_by_id(organisation_id)

        if not organisation:
            return dict(status='fail', message='Organisation not found'), 404

        org_admins = organisation.admins

        org_admin_data, errors = org_schema.dumps(org_admins)

        if errors:
            return dict(status="fail", message="Internal Server Error"), 500

        return dict(status="success", data=dict(organisation_admins=json.loads(org_admin_data))), 200


    # remove organisation admin

    def delete(self, organisation_id):
        """
        """
        org_admin_schema = OrgAdminSchema()

        org_admin_data = request.get_json()

        validated_org_admin_data, errors = org_admin_schema.load(org_admin_data)

        if errors:
            return dict(status='fail', message=errors), 400

        # Get User
        user = User.get_by_id(validated_org_admin_data.get('user_id', None))
        
        if not user:
            return dict(status='fail', message='User not found'), 404

        # Get organisation
        organisation = Organisation.get_by_id(organisation_id)

        if not organisation:
            return dict(status='fail', message='Organisation not found'), 404

        # removing user from organisation admins
        try:
            organisation.admins.remove(user)
        except Exception as e:
            return dict(status='fail', message='Organisation Admin not found'), 404

        saved_org_admins = organisation.save()

        if not saved_org_admins:
            return dict(status='fail', message='Internal Server Error'), 500
        
        org_schema = OrganisationSchema()

        new_org_admin_data, errors = org_schema.dumps(organisation)

        return dict(status='success', data=dict(organisation_admins=json.loads(new_org_admin_data))), 200
