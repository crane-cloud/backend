import json
import os
from flask_restful import Resource, request
from app.schemas import DatabaseFlavourSchema
from app.models.database_flavour import DatabaseFlavour
from flask_jwt_extended import jwt_required
from app.helpers.decorators import admin_required


class DatabaseFlavourView(Resource):

    @admin_required
    def post(self):
        """
        """
        flavour_schema = DatabaseFlavourSchema()

        flavour_data = request.get_json()

        validated_database_flavour_data, errors = flavour_schema.load(
            flavour_data)

        if errors:
            return dict(status="fail", message=errors), 400

        database_flavour_name = validated_database_flavour_data.get(
            'name', None)

        database_flavour_existant = DatabaseFlavour.find_first(
            name=database_flavour_name)

        if database_flavour_existant:
            return dict(
                status="fail",
                message=f" Database flavour {database_flavour_name} Already Exists."
            ), 400

        database = DatabaseFlavour(**validated_database_flavour_data)
        saved_database = database.save()

        if not saved_database:
            return dict(status='fail', message=f'Internal Server Error'), 500

        new_database_flavour_data, errors = flavour_schema.dumps(database)

        return dict(
            status='success',
            data=dict(database=json.loads(new_database_flavour_data))
        ), 201

    @jwt_required
    def get(self):
        """
        """
        flavour_schema = DatabaseFlavourSchema(many=True)

        database_flavours = DatabaseFlavour.find_all()

        database_flavour_data, errors = flavour_schema.dumps(database_flavours)

        if errors:
            return dict(status='fail', message=errors), 500

        return dict(status='success', data=dict(database_flavours=json.loads(database_flavour_data))), 200


class DatabaseFlavourDetailView(Resource):

    @admin_required
    def delete(self, database_flavour_id):
        """
        """
        flavour_schema = DatabaseFlavourSchema()

        database_flavour_existant = DatabaseFlavour.get_by_id(
            database_flavour_id)

        if not database_flavour_existant:
            return dict(
                status="fail",
                message=f" Database flavour with id {database_flavour_id} not found."
            ), 404

        deleted_database_flavour = database_flavour_existant.delete()

        if not deleted_database_flavour:
            return dict(status='fail', message=f'Internal Server Error'), 500

        return dict(status='success', message=" Database flavour Successfully deleted"), 200

    @jwt_required
    def get(self, database_flavour_id):
        """
        """
        flavour_schema = DatabaseFlavourSchema()

        database_flavour = DatabaseFlavour.get_by_id(database_flavour_id)

        if not database_flavour:
            return dict(
                status="fail",
                message=f" Database flavour with id {database_flavour_id} not found."
            ), 404

        database_flavour_data, errors = flavour_schema.dumps(database_flavour)

        if errors:
            return dict(status='fail', message=errors), 500

        return dict(status='success', data=dict(database=json.loads(database_flavour_data))), 200

    @admin_required
    def patch(self, database_flavour_id):
        """
        """

        flavour_schema = DatabaseFlavourSchema()

        database_flavour_data = request.get_json()

        validata_database_flavour_data, errors = flavour_schema.load(
            database_flavour_data)

        existing_database_flavour = False

        if errors:
            return dict(status='fail', message=errors), 400

        if 'name' in validata_database_flavour_data:
            existing_database_flavour = DatabaseFlavour.find_first(
                name=validata_database_flavour_data['name'])

        if existing_database_flavour:
            return dict(
                status='fail',
                message=f'Database flavour with name {validata_database_flavour_data["name"]} already exists'
            ), 409

        database_flavour = DatabaseFlavour.get_by_id(database_flavour_id)

        if not database_flavour:
            return dict(status='fail', message=f'Database flavour {database_flavour_id} not found'), 404

        updated_database_flavour = DatabaseFlavour.update(
            database_flavour, **validata_database_flavour_data)

        if not updated_database_flavour:
            return dict(status='fail', message='internal server error'), 500

        return dict(
            status='success',
            message=f'Database project {database_flavour_id} updated successfully'
        ), 200
