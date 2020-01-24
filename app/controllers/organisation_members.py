import json
from flask import current_app
from flask_restful import Resource, request
from app.schemas import OrganisationSchema
from app.schemas import OrgMemberSchema
from app.models.organisation_members import OrganisationMembers
from app.models.user import User
from app.models.organisation import Organisation


class OrgMemberView(Resource):

    def post(self):
        """
        """

        org_member_schema = OrgMemberSchema()

        org_member_data = request.get_json()

        validated_org_member_data, errors = org_member_schema.load(org_member_data)

        if errors:
            return dict(status='fail', message=errors), 400

        org_member = OrganisationMembers(**validated_org_member_data)

        saved_org_member = org_member.save()

        if not saved_org_member:
            return dict(status='fail', message='Internal Server Error'), 500

        new_org_member_data, errors = org_member_schema.dumps(org_member)

        return dict(status='success', data=dict(organisation_member=json.loads(new_org_member_data))), 201

    def get(self):
        """
        """
        org_member_schema = OrgMemberSchema(many=True)

        org_member = OrganisationMembers.find_all()

        org_member_data, errors = org_member_schema.dumps(org_member)

        if errors:
            return dict(status="fail", message="Internal Server Error"), 500

        return dict(status="success", data=dict(organisation_member=json.loads(org_member_data))), 200


class OrgMemberDetailView(Resource):

    def getOrgMembers(self, org_id):
        organisation = Organisation.find_first(id=org_id)
        if not organisation:
            return dict(status='fail', message='Internal Server Error'), 500
            # return False
        return organisation.users


    """ Get Users in an Organisation """
    def get(self, org_id):
        organisation_schema = OrganisationSchema(many=True)
        
        members = self.getOrgMembers(org_id)

        members_data, errors = organisation_schema.dumps(members)

        if errors:
            return dict(status="fail", message="Internal Server Error"), 500

        return dict(status="success", data=dict(members=json.loads(members_data))), 200

