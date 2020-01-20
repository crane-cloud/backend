import json
from flask_restful import Resource, request
from flask_jwt_extended import (
    jwt_required,
    get_jwt_identity,
)
from app.schemas import OrganisationSchema
from app.models.organisation import Organisation


class OrganisationsView(Resource):

    def post(self):
        """
        """

        org_schema = OrganisationSchema()

        org_data = request.get_json()

        validated_org_data, errors = org_schema.load(org_data)

        if errors:
            return dict(status='fail', message=errors), 400

        organisation = Organisation(**validated_org_data)

        saved_organisation = organisation.save()

        if not saved_organisation:
            return dict(status='fail', message='Internal Server Error'), 500

        new_org_data, errors = org_schema.dumps(organisation)

        return dict(status='success', data=dict(organisation=json.loads(new_org_data))), 201

    @jwt_required
    def get(self):
        """
        """

        org_schema = OrganisationSchema(many=True)

        organisations = Organisation.find_all()

        orgs_data, errors = org_schema.dumps(organisations)

        if errors:
            return dict(status="fail", message="Internal Server Error"), 500

        return dict(status="success", data=dict(organisations=json.loads(orgs_data))), 200


class OrganisationDetailView(Resource):

    def get(self, org_id):
        """
        """
        schema = OrganisationSchema()

        organisation = Organisation.get_by_id(org_id)

        if not organisation:
            return dict(status="fail", message=f"Organisation with id {org_id} not found"), 404

        org_data, errors = schema.dumps(organisation)

        if errors:
            return dict(status="fail", message=errors), 500

        return dict(status='success', data=dict(organisation=json.loads(org_data))), 200

    def patch(self, org_id):
        """
        """

        # To do check if user is admin
        schema = OrganisationSchema(partial=True)

        update_data = request.get_json()

        validated_update_data, errors = schema.load(update_data)

        if errors:
            return dict(status="fail", message=errors), 400

        organisation = Organisation.get_by_id(org_id)

        if not organisation:
            return dict(status="fail", message=f"Organisation with id {org_id} not found"), 404

        if 'name' in validated_update_data:
            organisation.name = validated_update_data['name']

        updated_organisation = organisation.save()

        if not updated_organisation:
            return dict(status='fail', message='Internal Server Error'), 500

        return dict(status="success", message="Organisation updated successfully"), 200

    def delete(self, org_id):
        """
        """

        # To do get current user and check if the user is admin

        organisation = Organisation.get_by_id(org_id)

        if not organisation:
            return dict(status="fail", message=f"Organisation with id {org_id} not found"), 404

        deleted_org = organisation.delete()

        if not deleted_org:
            return dict(status='fail', message='Internal Server Error'), 500

        return dict(status='success', message="Successfully deleted"), 200
