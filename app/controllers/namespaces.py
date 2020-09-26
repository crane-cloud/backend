import json
from flask_restful import Resource, request
from app.models.namespaces import Namespace
from app.models.organisation import Organisation
from app.schemas import NamespaceSchema


class NamespacesView(Resource):

    def get(self):
        """
        """
        schema = NamespaceSchema(many=True)

        namespaces = Namespace.find_all()

        namespace_data, errors = schema.dumps(namespaces)

        if errors:
            return dict(status='fail', message=errors), 500

        return dict(
            status='success',
            data=dict(namespaces=json.loads(namespace_data))
            ), 200


class NamespaceDetailView(Resource):

    def get(self, id):
        """
        """
        schema = NamespaceSchema()

        namespace = Namespace.get_by_id(id)

        if not namespace:
            return dict(
                status='fail',
                message=f'Namespace with id {id} not found'
                ), 404

        namespace_data, errors = schema.dumps(namespace)

        if errors:
            return dict(status="fail", message=errors), 500

        return dict(status='success', data=dict(
            namespace=json.loads(namespace_data))), 200

    def delete(self, id):
        """
        """
        namespace = Namespace.query.get(id)

        if not namespace:
            return dict(
                status='fail',
                message=f'Namespace with id {id} not found'
                ), 404

        deleted = namespace.delete()

        if not deleted:
            return dict(status='fail', message='Internal Server Error'), 500

        return dict(status='success', message='Successfully deleted'), 200


class OrganisationNamespaceView(Resource):

    def post(self, organisation_id):
        """
        """

        schema = NamespaceSchema()

        namespace_data = request.get_json()

        validated_namespace_data, errors = schema.load(namespace_data)

        if errors:
            return dict(status='fail', message=errors), 400

        organisation = Organisation.get_by_id(organisation_id)

        if not organisation:
            return dict(
                status='fail',
                message=f'Organisation with id {organisation_id} not found'
                ), 404

        name = validated_namespace_data.get('name')

        namespace = Namespace(name, organisation_id)
        saved = namespace.save()

        if not saved:
            return dict(status='fail', message='Internal Server Error'), 500

        new_namespace_data, errors = schema.dumps(namespace)

        return dict(status='success', data=dict(
            namespace=json.loads(new_namespace_data))), 201

    def get(self, organisation_id):
        """
        """
        schema = NamespaceSchema(many=True)

        organisation = Organisation.get_by_id(organisation_id)

        if not organisation:
            return dict(
                status='fail',
                message=f'Organisation with id {organisation_id} not found'
                ), 404

        namespaces = Namespace.query.filter_by(organisation_id=organisation.id)

        namespace_data, errors = schema.dumps(namespaces)

        if errors:
            return dict(status='fail', message=errors), 500

        return dict(status='success', data=dict(
            namespaces=json.loads(namespace_data))), 200
