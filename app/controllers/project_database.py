import json
from flask import current_app
from flask_restful import Resource, request
from app.schemas import ProjectDatabaseSchema
from app.models.project_database import ProjectDatabase
from app.helpers.database_service import DatabaseService
from app.models.project import Project
from flask_jwt_extended import jwt_required
from app.helpers.decorators import admin_required


class ProjectDatabaseView(Resource):

    @jwt_required
    def post(self, project_id):
        """
        """
        database_schema = ProjectDatabaseSchema()

        databases_data = request.get_json()

        validated_database_data, errors = database_schema.load(databases_data)

        database_name = validated_database_data.get('name', None)
        database_user = validated_database_data.get('user', None)

        if errors:
            return dict(status="fail", message=errors), 400

        project = Project.get_by_id(project_id)
        if not project:
            return dict(status='fail', message=f'Project with id {project_id} not found'), 404
        validated_database_data['project_id'] = project_id

        database_existant = ProjectDatabase.find_first(
            name=database_name)

        if database_existant:
            return dict(
                status="fail",
                message=f"Database {database_name} Already Exists."
            ), 400

        database_user_existant = ProjectDatabase.find_first(
            user=database_user)

        if database_user_existant:
            return dict(
                status="fail",
                message=f"Database user {database_user} Already Exists."
            ), 400

        # Create the databse
        database_service = DatabaseService()
        database_connection = database_service.create_connection()

        if not database_connection:
            return dict(
                status="fail",
                message=f"Failed to connect to the database service"
            ), 500

        create_database = database_service.create_database(
            db_name=database_name,
            user=validated_database_data.get('user', None),
            password=validated_database_data.get('password', None)
        )

        if not create_database:
            return dict(
                status="fail",
                message=f"Unable to create database"
            ), 500

        # Save database credentials
        database = ProjectDatabase(**validated_database_data)
        saved_database = database.save()

        if not saved_database:
            return dict(status='fail', message=f'Internal Server Error'), 500

        new_database_data, errors = database_schema.dumps(database)

        return dict(
            status='success',
            data=dict(database=json.loads(new_database_data))
        ), 201


class ProjectDatabaseDetailView(Resource):

    @jwt_required
    def get(self, project_id, database_id):
        """
        """
        database_schema = ProjectDatabaseSchema()

        project = Project.get_by_id(project_id)
        if not project:
            return dict(status='fail', message=f'Project with id {project_id} not found'), 404

        database = ProjectDatabase.get_by_id(database_id)

        if not database:
            return dict(
                status="fail",
                message=f"Database with id {database_id} not found."
            ), 404
        
        database_data, errors = database_schema.dumps(database)

        if errors:
            return dict(status='fail', message=errors), 500

        return dict(status='success', data=dict(database=json.loads(database_data))), 200

class ProjectDatabaseAdminView(Resource):
    @admin_required
    def post(self):
        """
        """
        database_schema = ProjectDatabaseSchema()

        databases_data = request.get_json()

        validated_database_data, errors = database_schema.load(databases_data)

        database_name = validated_database_data.get('name', None)
        database_user = validated_database_data.get('user', None)
        project_id = validated_database_data.get('project_id', None)

        if errors:
            return dict(status="fail", message=errors), 400

        if project_id:
            project = Project.get_by_id(project_id)
            if not project:
                return dict(status='fail', message=f'Project with id {project_id} not found'), 404

        database_existant = ProjectDatabase.find_first(
            name=database_name)

        if database_existant:
            return dict(
                status="fail",
                message=f"Database {database_name} Already Exists."
            ), 400

        database_user_existant = ProjectDatabase.find_first(
            user=database_user)

        if database_user_existant:
            return dict(
                status="fail",
                message=f"Database user {database_user} Already Exists."
            ), 400

        # Create the databse
        database_service = DatabaseService()
        database_connection = database_service.create_connection()

        if not database_connection:
            return dict(
                status="fail",
                message=f"Failed to connect to the database service"
            ), 500

        create_database = database_service.create_database(
            db_name=database_name,
            user=validated_database_data.get('user', None),
            password=validated_database_data.get('password', None)
        )

        if not create_database:
            return dict(
                status="fail",
                message=f"Unable to create database"
            ), 500

        # Save database credentials
        database = ProjectDatabase(**validated_database_data)
        saved_database = database.save()

        if not saved_database:
            return dict(status='fail', message=f'Internal Server Error'), 500

        new_database_data, errors = database_schema.dumps(database)

        return dict(
            status='success',
            data=dict(database=json.loads(new_database_data))
        ), 201
