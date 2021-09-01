import json
from flask_restful import Resource, request
from app.models.namespaces import Namespace
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
