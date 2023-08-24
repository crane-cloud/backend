from datetime import datetime
import json
import os
from app.schemas.monitoring_metrics import UserGraphSchema
from flask import current_app
from flask_restful import Resource, request
from app.schemas import ProjectDatabaseSchema
from app.models.project_database import ProjectDatabase
from app.helpers.database_service import MysqlDbService, PostgresqlDbService, generate_db_credentials
from app.models.project import Project
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt_claims
from app.helpers.decorators import admin_required
from app.helpers.db_flavor import get_db_flavour, database_flavours
from app.helpers.admin import is_authorised_project_user, is_owner_or_admin
from app.helpers.activity_logger import log_activity
from sqlalchemy import Date, func, column, cast, and_, select

from app.models import db


class ProjectDatabaseView(Resource):

    @jwt_required
    def post(self, project_id):
        """
        """
        current_user_id = get_jwt_identity()
        current_user_roles = get_jwt_claims()['roles']

        database_schema = ProjectDatabaseSchema()

        databases_data = request.get_json()

        credentials = generate_db_credentials()

        validated_database_data, errors = database_schema.load(databases_data)
        if errors:
            return dict(status="fail", message=errors), 400

        project = Project.get_by_id(project_id)
        if not project:
            return dict(status='fail', message=f'Project with id {project_id} not found'), 404

        if not is_owner_or_admin(project, current_user_id, current_user_roles):
            if not is_authorised_project_user(project, current_user_id, 'member'):
                return dict(status='fail', message='unauthorised'), 403

        database_flavour_name = validated_database_data.get(
            'database_flavour_name', None)

        db_flavour = get_db_flavour(database_flavour_name)

        if not db_flavour:
            return dict(
                status="fail",
                message=f"Database flavour with name {database_flavour_name} is not mysql or postgres."
            ), 409

        database_name = validated_database_data.get('name', credentials.name)
        database_user = validated_database_data.get('user', credentials.user)
        database_password = validated_database_data.get(
            'password', credentials.password)

        new_database_info = dict(
            user=database_user,
            password=database_password,
            project_id=project_id,
            name=database_name,
            database_flavour_name=database_flavour_name,
            host=db_flavour['host'],
            port=db_flavour['port']
        )

        validated_database_data, errors = database_schema.load(
            new_database_info)

        if errors:
            return dict(status="fail", message=errors), 400

        validated_database_data['project_id'] = project_id

        database_existant = ProjectDatabase.find_first(
            name=database_name)

        if database_existant:
            log_activity('Database', status='Failed',
                         operation='Create',
                         description=f'Database {database_name} Already Exists.',
                         a_project_id=project.id,
                         a_cluster_id=project.cluster_id)
            return dict(
                status="fail",
                message=f"Database {database_name} Already Exists."
            ), 400

        database_user_existant = ProjectDatabase.find_first(
            user=database_user)

        if database_user_existant:
            log_activity('Database', status='Failed',
                         operation='Create',
                         description=f'Database user {database_user} Already Exists',
                         a_project_id=project.id,
                         a_cluster_id=project.cluster_id)
            return dict(
                status="fail",
                message=f"Database user {database_user} Already Exists."
            ), 400

        # Create the database
        database_service = db_flavour['class']
        database_connection = database_service.check_db_connection()

        if not database_connection:
            log_activity('Database', status='Failed',
                         operation='Create',
                         description='Failed to connect to the database service, Internal Server Error',
                         a_project_id=project.id,
                         a_cluster_id=project.cluster_id)
            return dict(
                status="fail",
                message=f"Failed to connect to the database service"
            ), 500

        create_database = database_service.create_database(
            db_name=database_name,
            user=database_user,
            password=database_password
        )

        if not create_database:
            log_activity('Database', status='Failed',
                         operation='Create',
                         description=f'Database Creation Failed, Internal Server Error',
                         a_project_id=project.id,
                         a_cluster_id=project.cluster_id)
            return dict(
                status="fail",
                message=f"Unable to create database"
            ), 500

        # Save database credentials
        database = ProjectDatabase(**validated_database_data)
        saved_database = database.save()

        if not saved_database:
            log_activity('Database', status='Failed',
                         operation='Create',
                         description=f'Database Creation Failed, Internal Server Error',
                         a_project_id=project.id,
                         a_cluster_id=project.cluster_id)
            return dict(status='fail', message=f'Internal Server Error'), 500

        new_database_data, errors = database_schema.dumps(database)
        log_activity('Database', status='Success',
                     operation='Create',
                     description=f'Database {database_name} created successfully',
                     a_project_id=project.id,
                     a_cluster_id=project.cluster_id,
                     a_db_id=database.id)
        return dict(
            status='success',
            data=dict(database=json.loads(new_database_data))
        ), 201

    @jwt_required
    def get(self, project_id):
        """
        """
        current_user_id = get_jwt_identity()
        current_user_roles = get_jwt_claims()['roles']

        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)

        database_schema = ProjectDatabaseSchema(many=True)

        project = Project.get_by_id(project_id)
        if not project:
            return dict(status='fail', message=f'Project with id {project_id} not found'), 404

        if not is_owner_or_admin(project, current_user_id, current_user_roles):
            if not is_authorised_project_user(project, current_user_id, 'member'):
                return dict(status='fail', message='unauthorised'), 403

        databases = ProjectDatabase.find_all(
            project_id=project_id, paginate=True, page=page, per_page=per_page)

        database_data, errors = database_schema.dumps(databases.items)

        if errors:
            return dict(status='fail', message=errors), 500

        database_data_list = json.loads(database_data)
        pagination = databases.pagination

        # Check the database status on host
        for database in database_data_list:
            flavour_name = database['database_flavour_name']
            if not flavour_name:
                flavour_name = "mysql"

            db_flavour = get_db_flavour(flavour_name)
            database_service = db_flavour['class']

            try:
                database_connection = database_service.create_db_connection(
                    user=database['user'], password=database['password'], db_name=database['name'])

                if not database_connection:
                    db_status = False
                else:
                    db_status = True
            except:
                db_status = False
            finally:
                if database_connection:
                    if database_service == MysqlDbService():
                        if database_connection.is_connected():
                            database_connection.close()
                        else:
                            database_connection.close()

            database['db_status'] = db_status

        return dict(status='success', data=dict(pagination=pagination, databases=database_data_list)), 200


class ProjectDatabaseDetailView(Resource):

    @jwt_required
    def delete(self, project_id, database_id):
        """
        """
        current_user_id = get_jwt_identity()
        current_user_roles = get_jwt_claims()['roles']

        project = Project.get_by_id(project_id)
        if not project:
            return dict(status='fail', message=f'Project with id {project_id} not found'), 404

        if not is_owner_or_admin(project, current_user_id, current_user_roles):
            if not is_authorised_project_user(project, current_user_id, 'admin'):
                return dict(status='fail', message='unauthorised'), 403

        database_existant = ProjectDatabase.get_by_id(database_id)

        if not database_existant:
            return dict(
                status="fail",
                message=f"Database with id {database_id} not found."
            ), 404

        database_flavour_name = database_existant.database_flavour_name
        if not database_flavour_name:
            database_flavour_name = "mysql"

        db_flavour = get_db_flavour(database_flavour_name)

        if not db_flavour:
            return dict(
                status="fail",
                message=f"Database flavour with name {database_existant.database_flavour_name} is not mysql or postgres."
            ), 409

        # Delete the database
        database_service = db_flavour['class']
        database_connection = database_service.check_db_connection()

        if not database_connection:
            log_activity('Database', status='Failed',
                         operation='Delete',
                         description='Failed to connect to the database service, Internal Server Error',
                         a_project_id=project.id,
                         a_cluster_id=project.cluster_id,
                         a_db_id=database_id)
            return dict(
                status="fail",
                message=f"Failed to connect to the database service"
            ), 500

        delete_database = database_service.delete_database(
            database_existant.name)

        if not delete_database:
            log_activity('Database', status='Failed',
                         operation='Delete',
                         description='Unable to delete database, Internal Server Error',
                         a_project_id=project.id,
                         a_cluster_id=project.cluster_id,
                         a_db_id=database_id)
            return dict(
                status="fail",
                message=f"Unable to delete database"
            ), 500

        # Delete database record from database
        deleted_database = database_existant.soft_delete()

        if not deleted_database:
            log_activity('Database', status='Failed',
                         operation='Delete',
                         description=f'Database {database_id} deleted Failed, Internal Server Error',
                         a_project_id=project.id,
                         a_cluster_id=project.cluster_id,
                         a_db_id=database_id)
            return dict(status='fail', message=f'Internal Server Error'), 500
        log_activity('Database', status='Success',
                     operation='Delete',
                     description=f'Database {database_id} deleted successfully',
                     a_project_id=project.id,
                     a_cluster_id=project.cluster_id,
                     a_db_id=database_id)
        return dict(status='success', message="Database Successfully deleted"), 200

    @jwt_required
    def get(self, project_id, database_id):
        """
        """
        current_user_id = get_jwt_identity()
        current_user_roles = get_jwt_claims()['roles']

        database_schema = ProjectDatabaseSchema()

        project = Project.get_by_id(project_id)
        if not project:
            return dict(status='fail', message=f'Project with id {project_id} not found'), 404

        if not is_owner_or_admin(project, current_user_id, current_user_roles):
            if not is_authorised_project_user(project, current_user_id, 'member'):
                return dict(status='fail', message='unauthorised'), 403

        database_existant = ProjectDatabase.get_by_id(database_id)

        if not database_existant:
            return dict(
                status="fail",
                message=f"Database with id {database_id} not found."
            ), 404

        database_data, errors = database_schema.dumps(database_existant)

        if errors:
            return dict(status='fail', message=errors), 500

        # Check the database status on host
        flavour_name = database_existant.database_flavour_name
        if not flavour_name:
            flavour_name = "mysql"

        db_flavour = get_db_flavour(flavour_name)

        if not db_flavour:
            return dict(
                status="fail",
                message=f"Database with flavour {database_existant.database_flavour_name} is not mysql or postgres."
            ), 409

        database_service = db_flavour['class']

        # Get db status
        try:
            database_connection = database_service.create_db_connection(
                user=database_existant.user, password=database_existant.password, db_name=database_existant.name)
            if not database_connection:
                db_status = False
            else:
                db_status = True
        except:
            db_status = False
        finally:
            if database_connection:
                if database_service == MysqlDbService():
                    if database_connection.is_connected():
                        database_connection.close()
                    else:
                        database_connection.close()

        database_data_list = json.loads(database_data)
        database_data_list['db_status'] = db_status
        database_data_list['db_size'] = database_service.get_database_size(
            user=database_existant.user, password=database_existant.password, db_name=database_existant.name)

        return dict(status='success', data=dict(database=database_data_list)), 200


class ProjectDatabasePasswordResetView(Resource):

    @jwt_required
    def post(self, project_id, database_id):
        """
        """
        current_user_id = get_jwt_identity()
        current_user_roles = get_jwt_claims()['roles']

        database_schema = ProjectDatabaseSchema()
        database_data = request.get_json()

        validated_database_data, errors = database_schema.load(
            database_data, partial=("database_flavour_name",))

        if errors:
            return dict(status="fail", message=errors), 400

        new_database_password = validated_database_data.get(
            'password', None)

        project = Project.get_by_id(project_id)
        if not project:
            return dict(status='fail', message=f'Project with id {project_id} not found'), 404

        if not is_owner_or_admin(project, current_user_id, current_user_roles):
            if not is_authorised_project_user(project, current_user_id, 'admin'):
                return dict(status='fail', message='unauthorised'), 403

        database_existant = ProjectDatabase.get_by_id(database_id)
        if not database_existant:
            return dict(
                status="fail",
                message=f"Database with id {database_id} not found."
            ), 404

        database_flavour_name = database_existant.database_flavour_name

        db_flavour = get_db_flavour(database_flavour_name)

        if not db_flavour:
            return dict(
                status="fail",
                message=f"Database flavour with name {database_existant.database_flavour_name} is not mysql or postgres."
            ), 409

        # Reset db password
        database_service = db_flavour['class']
        database_connection = database_service.check_db_connection()

        if not database_connection:
            log_activity('Database', status='Failed',
                         operation='Update',
                         description='Failed to connect to the database service, Internal Server Error',
                         a_project_id=project.id,
                         a_cluster_id=project.cluster_id,
                         a_db_id=database_id)
            return dict(
                status="fail",
                message=f"Failed to connect to the database service"
            ), 500

        reset_database_password = database_service.reset_password(user=database_existant.user,
                                                                  password=new_database_password)

        if not reset_database_password:
            log_activity('Database', status='Failed',
                         operation='Update',
                         description='Unable to reset database password, Internal Server Error',
                         a_project_id=project.id,
                         a_cluster_id=project.cluster_id,
                         a_db_id=database_id)
            return dict(
                status="fail",
                message=f"Unable to reset database password"
            ), 500

        updated = ProjectDatabase.update(
            database_existant, **validated_database_data)
        if not updated:
            log_activity('Database', status='Failed',
                         operation='Update',
                         description='Unable to reset database, Internal Server Error',
                         a_project_id=project.id,
                         a_cluster_id=project.cluster_id,
                         a_db_id=database_id)
            return dict(status='fail', message='internal server error'), 500

        log_activity('Database', status='Success',
                     operation='Update',
                     description='Database password reset Successfully',
                     a_project_id=project.id,
                     a_cluster_id=project.cluster_id,
                     a_db_id=database_id)
        return dict(status='success', message="Database password reset Successfully"), 200


class ProjectDatabaseRetrievePasswordView(Resource):

    @jwt_required
    def get(self, project_id, database_id):
        """
        """
        current_user_id = get_jwt_identity()
        current_user_roles = get_jwt_claims()['roles']

        database_schema = ProjectDatabaseSchema()

        project = Project.get_by_id(project_id)

        if not project:
            return dict(status='fail', message=f'Project with id {project_id} not found'), 404

        if not is_owner_or_admin(project, current_user_id, current_user_roles):
            if not is_authorised_project_user(project, current_user_id, 'member'):
                return dict(status='fail', message='unauthorised'), 403

        database_existant = ProjectDatabase.get_by_id(database_id)

        if not database_existant:
            return dict(
                status="fail",
                message=f"Database with id {database_id} not found."
            ), 404

        password_data = dict(password=database_existant.password)

        database_password_data, errors = database_schema.dumps(password_data)

        if errors:
            return dict(status='fail', message=errors), 500

        return dict(status='success', data=json.loads(database_password_data)), 200


class ProjectDatabaseAdminView(Resource):
    @admin_required
    def post(self):
        """
        """
        database_schema = ProjectDatabaseSchema()

        databases_data = request.get_json()

        credentials = generate_db_credentials()

        validated_database_data, errors = database_schema.load(databases_data)

        if errors:
            return dict(status="fail", message=errors), 400

        database_flavour_name = validated_database_data.get(
            'database_flavour_name', None)

        db_flavour = get_db_flavour(database_flavour_name)

        if not db_flavour:
            return dict(
                status="fail",
                message=f"Database with flavour name {database_flavour_name} is not mysql or postgres."
            ), 409

        database_name = validated_database_data.get('name', credentials.name)
        database_user = validated_database_data.get('user', credentials.user)
        database_password = validated_database_data.get(
            'password', credentials.password)
        project_id = validated_database_data.get('project_id', None)

        new_database_info = dict(
            user=database_user,
            password=database_password,
            project_id=project_id,
            name=database_name,
            database_flavour_name=database_flavour_name,
            host=db_flavour['host'],
            port=db_flavour['port']
        )

        if project_id:
            project = Project.get_by_id(project_id)
            if not project:
                return dict(status='fail', message=f'Project with id {project_id} not found'), 404
        else:
            del new_database_info["project_id"]

        validated_database_data, errors = database_schema.load(
            new_database_info)

        if errors:
            return dict(status="fail", message=errors), 400

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

        # Create the database
        database_service = db_flavour['class']
        database_connection = database_service.check_db_connection()

        if not database_connection:
            log_activity('Database', status='Failed',
                         operation='Create',
                         description='Admin Failed to connect to the database service, Internal Server Error',
                         a_project_id=project.id,
                         a_cluster_id=project.cluster_id,)
            return dict(
                status="fail",
                message=f"Failed to connect to the database service"
            ), 500

        create_database = database_service.create_database(
            db_name=database_name,
            user=database_user,
            password=database_password
        )

        if not create_database:
            log_activity('Database', status='Failed',
                         operation='Create',
                         description='Admin Unable, Internal Server Error',
                         a_project_id=project.id,
                         a_cluster_id=project.cluster_id,)
            return dict(
                status="fail",
                message=f"Unable to create database"
            ), 500

        # Save database credentials
        database = ProjectDatabase(**validated_database_data)
        saved_database = database.save()

        if not saved_database:
            log_activity('Database', status='Failed',
                         operation='Create',
                         description='Admin Created Database Failed, Internal Server Error',
                         a_project_id=project.id,
                         a_cluster_id=project.cluster_id,)
            return dict(status='fail', message=f'Internal Server Error'), 500

        new_database_data, errors = database_schema.dumps(database)
        log_activity('Database', status='Success',
                     operation='Create',
                     description='Admin Created Database Successfully',
                     a_project_id=project.id,
                     a_cluster_id=project.cluster_id,
                     a_db_id=database.id)
        return dict(
            status='success',
            data=dict(database=json.loads(new_database_data))
        ), 201

    @admin_required
    def get(self):
        """
        """
        database_schema = ProjectDatabaseSchema(many=True)

        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        flavour = request.args.get('db_flavour', None)
        if flavour:
            valid_flavour = get_db_flavour(flavour)
            if not valid_flavour:
                return dict(status='fail', message='Not a valid database flavour use mysql or postgres'), 401
            databases = ProjectDatabase.find_all(
                database_flavour_name=flavour, paginate=True, page=page, per_page=per_page)
        else:
            databases = ProjectDatabase.find_all(
                paginate=True, page=page, per_page=per_page)

        pagination = databases.pagination

        # Metadata
        metadata = dict()
        query = ProjectDatabase.query
        metadata['total'] = query.count()
        metadata['postgres_total'] = query.filter_by(
            database_flavour_name='postgres').count()
        metadata['mysql_total'] = query.filter_by(
            database_flavour_name='mysql').count()
        metadata['mysql_total'] = query.filter_by(
            database_flavour_name='mysql').count()
        db_user = ProjectDatabase.user
        metadata['users_number'] = query.with_entities(
            db_user, func.count(db_user)).group_by(db_user).distinct().count()

        database_data, errors = database_schema.dumps(databases.items)

        if errors:
            return dict(status='fail', message=errors), 500

        database_data_list = json.loads(database_data)

        return dict(status='success',  data=dict(metadata=metadata, pagination=pagination, databases=database_data_list)), 200


class ProjectDatabaseGraphAdminView(Resource):

    @admin_required
    def get(self):
        """
        Shows databases graph data
        """
        graph_filter_data = {
            'start': request.args.get('start', '2018-01-01'),
            'end': request.args.get('end', datetime.now().strftime('%Y-%m-%d')),
            'set_by': request.args.get('set_by', 'month')
        }
        flavour = request.args.get('db_flavour', None)
        if flavour:
            valid_flavour = get_db_flavour(flavour)
            if not valid_flavour:
                return dict(status='fail', message='Not a valid database flavour use mysql or postgres'), 401

        filter_schema = UserGraphSchema()

        validated_query_data, errors = filter_schema.load(graph_filter_data)
        if errors:
            return dict(status='fail', message=errors), 400

        start = validated_query_data.get('start')
        end = validated_query_data.get('end')
        set_by = validated_query_data.get('set_by')

        if set_by == 'month':
            date_list = func.generate_series(
                start, end, '1 month').alias('month')
            month = column('month')
            query = db.session.query(month, func.count(ProjectDatabase.id)).\
                select_from(date_list).\
                outerjoin(ProjectDatabase, func.date_trunc(
                    'month', ProjectDatabase.date_created) == month)
            if flavour:
                query = query.filter(
                    ProjectDatabase.database_flavour_name == flavour)

            db_data = query.group_by(month).order_by(month).all()

        else:
            date_list = func.generate_series(
                start, end, '1 year').alias('year')
            year = column('year')
            query = db.session.query(year, func.count(ProjectDatabase.id)).\
                select_from(date_list).\
                outerjoin(ProjectDatabase, func.date_trunc(
                    'year', ProjectDatabase.date_created) == year)

            if flavour:
                query = query.filter(
                    ProjectDatabase.database_flavour_name == flavour)

            db_data = query.group_by(year).order_by(year).all()

        db_info = []
        for item in db_data:
            item_dict = {
                'year': item[0].year, 'month': item[0].month, 'value': item[1]
            }
            db_info.append(item_dict)

        # Metadata
        metadata = dict()
        query = ProjectDatabase.query
        metadata['total'] = query.count()
        metadata['postgres_total'] = query.filter_by(
            database_flavour_name='postgres').count()
        metadata['mysql_total'] = query.filter_by(
            database_flavour_name='mysql').count()
        metadata['mysql_total'] = query.filter_by(
            database_flavour_name='mysql').count()
        db_user = ProjectDatabase.user
        metadata['users_number'] = query.with_entities(
            db_user, func.count(db_user)).group_by(db_user).distinct().count()

        return dict(status='success',  data=dict(metadata=metadata, graph_data=db_info)), 200


class ProjectDatabaseAdminDetailView(Resource):

    @admin_required
    def delete(self, database_id):
        """
        """
        database_schema = ProjectDatabaseSchema()

        database_existant = ProjectDatabase.get_by_id(database_id)

        if not database_existant:
            return dict(
                status="fail",
                message=f"Database with id {database_id} not found."
            ), 404

        project = database_existant.project
        db_flavour = get_db_flavour(database_existant.database_flavour_name)
        if not db_flavour:
            return dict(
                status="fail",
                message=f"Database with flavour name {database_existant.database_flavour_name} is not mysql or postgres."
            ), 409

        # Delete the database
        database_service = db_flavour['class']
        database_connection = database_service.check_db_connection()

        if not database_connection:
            log_activity('Database', status='Failed',
                         operation='Delete',
                         description='Failed to connect to the database service, Internal Server Error',
                         a_project_id=project.id,
                         a_cluster_id=project.cluster_id,
                         a_db_id=database_id)
            return dict(
                status="fail",
                message=f"Failed to connect to the database service"
            ), 500

        delete_database = database_service.delete_database(
            database_existant.name)

        if not delete_database:
            log_activity('Database', status='Failed',
                         operation='Delete',
                         description='Unable to delete database, Internal Server Error',
                         a_project_id=project.id,
                         a_cluster_id=project.cluster_id,
                         a_db_id=database_id)
            return dict(
                status="fail",
                message=f"Unable to delete database"
            ), 500

        # Delete database record from database
        deleted_database = database_existant.soft_delete()

        if not deleted_database:
            log_activity('Database', status='Failed',
                         operation='Delete',
                         description=f'Admin Delete Database {database_id} Failed, Internal Server Error',
                         a_project_id=project.id,
                         a_cluster_id=project.cluster_id,
                         a_db_id=database_id)
            return dict(status='fail', message=f'Internal Server Error'), 500
        log_activity('Database', status='Success',
                     operation='Delete',
                     description=f'Admin Deleted Database {database_id} Successfully',
                     a_project_id=project.id,
                     a_cluster_id=project.cluster_id,
                     a_db_id=database_id)
        return dict(status='success', message="Database Successfully deleted"), 200

    @admin_required
    def get(self, database_id):
        """
        """
        database_schema = ProjectDatabaseSchema()

        database_existant = ProjectDatabase.get_by_id(database_id)

        if not database_existant:
            return dict(
                status="fail",
                message=f"Database with id {database_id} not found."
            ), 404

        database_data, errors = database_schema.dumps(database_existant)

        if errors:
            return dict(status='fail', message=errors), 500

        # Check the database status on host
        flavour_name = database_existant.database_flavour_name

        if not flavour_name:
            flavour_name = "mysql"

        db_flavour = get_db_flavour(flavour_name)

        if not db_flavour:
            return dict(
                status="fail",
                message=f"Database with flavour name {database_existant.database_flavour_name} is not mysql or postgres."
            ), 409

        # Get db status
        database_service = db_flavour['class']
        try:
            database_connection = database_service.create_db_connection(
                user=database_existant.user, password=database_existant.password, db_name=database_existant.name)
            if not database_connection:
                db_status = False
            else:
                db_status = True
        except:
            db_status = False
        finally:
            if database_connection:
                if database_service == MysqlDbService():
                    if database_connection.is_connected():
                        database_connection.close()
                else:
                    database_connection.close()

        database_data_list = json.loads(database_data)
        database_data_list['db_status'] = db_status

        return dict(status='success', data=dict(database=database_data_list)), 200


class ProjectDatabaseResetView(Resource):

    @jwt_required
    def post(self, project_id, database_id):
        """
        Reset Database
        """
        current_user_id = get_jwt_identity()
        current_user_roles = get_jwt_claims()['roles']

        project = Project.get_by_id(project_id)
        if not project:
            return dict(status='fail', message=f'Project with id {project_id} not found'), 404

        if not is_owner_or_admin(project, current_user_id, current_user_roles):
            if not is_authorised_project_user(project, current_user_id, 'admin'):
                return dict(status='fail', message='unauthorised'), 403

        database_existant = ProjectDatabase.get_by_id(database_id)

        if not database_existant:
            return dict(
                status="fail",
                message=f"Database with id {database_id} not found."
            ), 404

        # Reset the database
        db_flavour = get_db_flavour(database_existant.database_flavour_name)

        if not db_flavour:
            return dict(
                status="fail",
                message=f"Database with flavour name {database_existant.database_flavour_name} is not mysql or postgres."
            ), 409

        database_service = db_flavour['class']
        database_connection = database_service.check_db_connection()

        if not database_connection:
            log_activity('Database', status='Failed',
                         operation='Update',
                         description=f'Reset Database Failed to connect to the database service, Internal Server Error',
                         a_project_id=project.id,
                         a_cluster_id=project.cluster_id,
                         a_db_id=database_id)
            return dict(
                status="fail",
                message=f"Failed to connect to the database service"
            ), 500

        reset_database = database_service.reset_database(
            db_name=database_existant.name,
            user=database_existant.user,
            password=database_existant.password
        )

        if not reset_database:
            log_activity('Database', status='Failed',
                         operation='Update',
                         description=f'Reset Database {database_id} Failed, Internal Server Error',
                         a_project_id=project.id,
                         a_cluster_id=project.cluster_id,
                         a_db_id=database_id)
            return dict(
                status="fail",
                message=f"Unable to reset database"
            ), 500
        log_activity('Database', status='Success',
                     operation='Update',
                     description=f'Reset Database {database_id} Successfully',
                     a_project_id=project.id,
                     a_cluster_id=project.cluster_id,
                     a_db_id=database_id)
        return dict(status='success', message="Database Reset Successfully"), 200


class ProjectDatabaseAdminResetView(Resource):

    @admin_required
    def post(self, database_id):
        """
        Reset Database
        """
        database_schema = ProjectDatabaseSchema()

        database_existant = ProjectDatabase.get_by_id(database_id)

        if not database_existant:
            return dict(
                status="fail",
                message=f"Database with id {database_id} not found."
            ), 404
        project = database_existant.project
        # Reset the database
        db_flavour = get_db_flavour(database_existant.database_flavour_name)

        if not db_flavour:
            return dict(
                status="fail",
                message=f"Database with flavour name {database_existant.database_flavour_name} is not mysql or postgres."
            ), 409

        database_service = db_flavour['class']

        database_connection = database_service.check_db_connection()

        if not database_connection:
            log_activity('Database', status='Failed',
                         operation='Update',
                         description=f'Admin Reset Database Failed to connect to the database service, Internal Server Error',
                         a_project_id=project.id,
                         a_cluster_id=project.cluster_id,
                         a_db_id=database_id)
            return dict(
                status="fail",
                message=f"Failed to connect to the database service"
            ), 500

        reset_database = database_service.reset_database(
            db_name=database_existant.name,
            user=database_existant.user,
            password=database_existant.password
        )

        if not reset_database:
            log_activity('Database', status='Failed',
                         operation='Update',
                         description=f'Admin Reset Database {database_id} Failed, Internal Server Error',
                         a_project_id=project.id,
                         a_cluster_id=project.cluster_id,
                         a_db_id=database_id)
            return dict(
                status="fail",
                message=f"Unable to reset database"
            ), 500
        log_activity('Database', status='Success',
                     operation='Update',
                     description=f'Admin Reset Database {database_id} Successfully',
                     a_project_id=project.id,
                     a_cluster_id=project.cluster_id,
                     a_db_id=database_id)
        return dict(status='success', message="Database Reset Successfully"), 200


class ProjectDatabaseAdminPasswordResetView(Resource):

    @admin_required
    def post(self, database_id):
        """
        """
        database_schema = ProjectDatabaseSchema()
        database_data = request.get_json()

        validated_database_data, errors = database_schema.load(
            database_data, partial=("database_flavour_name",))
        if errors:
            return dict(status="fail", message=errors), 400

        new_database_password = validated_database_data.get(
            'password', None)

        database_existant = ProjectDatabase.get_by_id(database_id)
        if not database_existant:
            return dict(
                status="fail",
                message=f"Database with id {database_id} not found."
            ), 404
        project = database_existant.project
        database_flavour_name = database_existant.database_flavour_name
        db_flavour = get_db_flavour(database_flavour_name)

        if not db_flavour:
            return dict(
                status="fail",
                message=f"Database flavour with name {database_existant.database_flavour_name} is not mysql or postgres."
            ), 409

        # Reset db password
        database_service = db_flavour['class']
        database_connection = database_service.check_db_connection()

        if not database_connection:
            log_activity('Database', status='Failed',
                         operation='Update',
                         description='Failed to connect to the database service, internal server error',
                         a_project_id=project.id,
                         a_cluster_id=project.cluster_id,
                         a_db_id=database_id)
            return dict(
                status="fail",
                message=f"Failed to connect to the database service"
            ), 500

        reset_database_password = database_service.reset_password(user=database_existant.user,
                                                                  password=new_database_password)

        if not reset_database_password:
            log_activity('Database', status='Failed',
                         operation='Update',
                         description='Unable to reset database password, internal server error',
                         a_project_id=project.id,
                         a_cluster_id=project.cluster_id,
                         a_db_id=database_id)
            return dict(
                status="fail",
                message=f"Unable to reset database password"
            ), 500

        updated = ProjectDatabase.update(
            database_existant, **validated_database_data)

        if not updated:
            log_activity('Database', status='Failed',
                         operation='Update',
                         description='Database password reset Failed, internal server error',
                         a_project_id=project.id,
                         a_cluster_id=project.cluster_id,
                         a_db_id=database_id)
            return dict(status='fail', message='internal server error'), 500
        log_activity('Database', status='Success',
                     operation='Update',
                     description='Database password reset Successfully',
                     a_project_id=project.id,
                     a_cluster_id=project.cluster_id,
                     a_db_id=database_id)
        return dict(status='success', message="Database password reset Successfully"), 200


class ProjectDatabaseAdminRetrievePasswordView(Resource):

    @admin_required
    def get(self, database_id):
        """
        """
        database_schema = ProjectDatabaseSchema()

        database_existant = ProjectDatabase.get_by_id(database_id)

        if not database_existant:
            return dict(
                status="fail",
                message=f"Database with id {database_id} not found."
            ), 404

        password_data = dict(password=database_existant.password)

        database_password_data, errors = database_schema.dumps(password_data)

        if errors:
            return dict(status='fail', message=errors), 500

        return dict(status='success', data=json.loads(database_password_data)), 200


class DatabaseStatsView(Resource):
    @admin_required
    def get(self):
        """
        """

        # get databases count per flavour
        dbs_per_flavour = {}
        tot_database_count = 0
        for flavour in database_flavours:
            databases = ProjectDatabase.find_all(
                database_flavour_name=flavour['name'])
            database_count = len(databases)
            dbs_per_flavour[f"{flavour['name']}_db_count"] = database_count

            tot_database_count = tot_database_count + database_count

        data = dict(total_database_count=tot_database_count,
                    dbs_stats_per_flavour=dbs_per_flavour)

        return dict(status='Success',
                    data=dict(databases=data)), 200
