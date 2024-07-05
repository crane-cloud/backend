import json
from flask_restful import Resource, request
from flask_jwt_extended import jwt_required
from marshmallow import ValidationError
from app.models.registry import Registry
from app.schemas import RegistrySchema


class RegistriesView(Resource):

    @jwt_required()
    def get(self):
        """
        """
        registery_schema = RegistrySchema(many=True)

        registries = Registry.find_all()

        try:
            validated_reg_data = registery_schema.dumps(registries)
        except ValidationError:
            return dict(status='fail', message='Internal Server Error'), 500

        return dict(status='success',
                    data=dict(registries=json.loads(validated_reg_data))), 200
