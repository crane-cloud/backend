import json
from flask import current_app
from flask_restful import Resource, request
from app.schemas import OrganisationSchema, OrgMemberSchema, UserSchema
from app.models.organisation_members import OrganisationMembers
from app.models.user import User
from app.models.organisation import Organisation


class OrgMemberView(Resource):

    def post(self, organisation_id):
        """
        """

        org_member_schema = OrgMemberSchema()

        org_member_data = request.get_json()

        validated_org_member_data, errors = org_member_schema.load(org_member_data)

        if errors:
            return dict(status='fail', message=errors), 400


        # Get User
        user = User.get_by_id(validated_org_member_data.get('user_id', None))
        
        if not user:
            return dict(status='fail', message='User not found'), 404

        # Get organisation
        organisation = Organisation.get_by_id(organisation_id)

        if not organisation:
            return dict(status='fail', message='Organisation not found'), 404

        if user in organisation.members:
            return dict(status='fail', message='Member already exist'), 409

        # adding user to organisation members
        organisation.members.append(user)

        saved_org_member = organisation.save()

        user_schema = UserSchema()

        if not saved_org_member:
            return dict(status='fail', message='Internal Server Error'), 500

        new_org_member_data, errors = user_schema.dumps(user)

        return dict(status='success', data=dict(organisation_member=json.loads(new_org_member_data))), 201


    def get(self, organisation_id):
        """
        """
        org_schema = OrganisationSchema(many=True)

        organisation = Organisation.get_by_id(organisation_id)

        if not organisation:
            return dict(status='fail', message='Organisation not found'), 404

        org_members = organisation.members

        org_member_data, errors = org_schema.dumps(org_members)

        if errors:
            return dict(status="fail", message="Internal Server Error"), 500

        return dict(status="success", data=dict(organisation_member=json.loads(org_member_data))), 200


    # delete user role

    def delete(self, organisation_id):
        """
        """
        org_member_schema = OrgMemberSchema()

        org_member_data = request.get_json()

        validated_org_member_data, errors = org_member_schema.load(org_member_data)

        if errors:
            return dict(status='fail', message=errors), 400

        # Get User
        user = User.get_by_id(validated_org_member_data.get('user_id', None))
        
        if not user:
            return dict(status='fail', message='User not found'), 404

        # Get organisation
        organisation = Organisation.get_by_id(organisation_id)

        if not organisation:
            return dict(status='fail', message='Organisation not found'), 404

        # removing user from organisation
        try:
            organisation.members.remove(user)
        except Exception as e:
            return dict(status='fail', message='Organisation member not found'), 404

        saved_org_members = organisation.save()

        if not saved_org_members:
            return dict(status='fail', message='Internal Server Error'), 500
        
        org_schema = OrganisationSchema()

        new_org_member_data, errors = org_schema.dumps(organisation)

        return dict(status='success', data=dict(org_members=json.loads(new_org_member_data))), 201
