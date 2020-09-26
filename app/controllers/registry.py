import json
from flask_restful import Resource, request
from flask_jwt_extended import jwt_required
from app.models.registry import Registry
from app.schemas import RegistrySchema


class RegistriesView(Resource):

    @jwt_required
    def get(self):
        """
        """
        registery_schema = RegistrySchema(many=True)

        registries = Registry.find_all()

        validated_reg_data, errors = registery_schema.dumps(registries)

        if errors:
            return dict(status='fail', message='Internal Server Error'), 500
  
        return dict(status='success',
                    data=dict(registries=json.loads(validated_reg_data))), 200
