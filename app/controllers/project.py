import json
from flask_restful import Resource, request
from kubernetes import client
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt_claims

from app.schemas import ProjectSchema
from app.models.project import Project
from app.models.clusters import Cluster
from app.models.user import User
from app.helpers.kube import create_kube_clients
from app.helpers.role_search import has_role
from app.helpers.admin import is_owner_or_admin, is_current_or_admin
from app.helpers.alias import create_alias


class ProjectsView(Resource):

    @jwt_required
    def post(self):
        """
        """

        current_user_id = get_jwt_identity()
        current_user_roles = get_jwt_claims()['roles']

        project_schema = ProjectSchema()

        project_data = request.get_json()

        validated_project_data, errors = project_schema.load(project_data)

        if errors:
            return dict(status='fail', message=errors), 400

        if not has_role(current_user_roles, 'administrator'):
            validated_project_data['owner_id'] = current_user_id

        # check if project already exists
        existing_project = Project.find_first(
            name=validated_project_data['name'],
            owner_id=validated_project_data['owner_id'])

        if existing_project:
            return dict(
                status='fail',
                message=f'project with name {validated_project_data["name"]} already exists'), 409

        try:
            validated_project_data['alias'] = create_alias(validated_project_data['name'])
            namespace_name = validated_project_data['alias']
            cluster_id = validated_project_data['cluster_id']
            cluster = Cluster.get_by_id(cluster_id)

            if not cluster:
                return dict(status='fail', message=f'cluster {cluster_id} not found'), 404

            kube_host = cluster.host
            kube_token = cluster.token

            kube, extension_api, appsv1_api, api_client, batchv1_api, storageV1Api = create_kube_clients(kube_host, kube_token)

            # create namespace in cluster
            cluster_namespace = kube.create_namespace(
                client.V1Namespace(
                    metadata=client.V1ObjectMeta(name=namespace_name)
                    ))
            # create project in database
            if cluster_namespace:
                project = Project(**validated_project_data)

                saved = project.save()

                if not saved:
                    # delete the namespace
                    kube.delete_namespace(namespace_name)
                    return dict(status='fail', message='Internal Server Error'), 500

            new_project_data, errors = project_schema.dump(project)

            return dict(status='success', data=dict(project=new_project_data)), 201

        except client.rest.ApiException as e:
            return dict(status='fail', message=e.reason), e.status

        except Exception as err:
            return dict(status='fail', message=str(err)), 500

    @jwt_required
    def get(self):
        """
        """

        current_user_id = get_jwt_identity()
        current_user_roles = get_jwt_claims()['roles']

        project_schema = ProjectSchema(many=True)

        if has_role(current_user_roles, 'administrator'):
            projects = Project.find_all()
        else:
            projects = Project.find_all(owner_id=current_user_id)

        project_data, errors = project_schema.dumps(projects)

        if errors:
            return dict(status='fail', message=errors), 500

        return dict(status='success', data=dict(projects=json.loads(project_data))), 200


class ProjectDetailView(Resource):

    @jwt_required
    def get(self, project_id):
        """
        """
        current_user_id = get_jwt_identity()
        current_user_roles = get_jwt_claims()['roles']

        project_schema = ProjectSchema()

        project = Project.get_by_id(project_id)

        if not project:
            return dict(status='fail', message=f'project {project_id} not found'), 404

        if not is_owner_or_admin(project, current_user_id, current_user_roles):
            return dict(status='fail', message='unauthorised'), 403

        project_data, errors = project_schema.dumps(project)

        if errors:
            return dict(status='fail', message=errors), 500

        return dict(status='success', data=dict(
            project=json.loads(project_data))), 200

    @jwt_required
    def delete(self, project_id):
        """
        """

        try:
            current_user_id = get_jwt_identity()
            current_user_roles = get_jwt_claims()['roles']

            project = Project.get_by_id(project_id)

            if not project:
                return dict(status='fail', message=f'project {project_id} not found'), 404

            if not is_owner_or_admin(project, current_user_id, current_user_roles):
                return dict(status='fail', message='unauthorised'), 403

            # get cluster for the project
            cluster = Cluster.get_by_id(project.cluster_id)

            if not cluster:
                return dict(status='fail', message='cluster not found'), 500

            kube_host = cluster.host
            kube_token = cluster.token

            kube, extension_api, appsv1_api, api_client, batchv1_api, storageV1Api = create_kube_clients(kube_host, kube_token)

            # get corresponding namespace

            namespace = kube.read_namespace(project.alias)

            # delete namespace if it exists
            if namespace:
                kube.delete_namespace(project.alias)

            # To do; change delete to a soft delete
            deleted = project.delete()

            if not deleted:
                return dict(status='fail', message='deletion failed'), 500

            return dict(status='success', message=f'project {project_id} deleted successfully'), 200
        except client.rest.ApiException as e:
            return dict(status='fail', message=e.reason), e.status

        except Exception as e:
            return dict(status='fail', message=str(e)), 500

    @jwt_required
    def patch(self, project_id):
        """
        """

        try:
            current_user_id = get_jwt_identity()
            current_user_roles = get_jwt_claims()['roles']

            project_schema = ProjectSchema(only=("name", "description"), partial=True)

            project_data = request.get_json()

            validate_project_data, errors = project_schema.load(project_data)
            
            existing_project = False

            if errors:
                return dict(status='fail', message=errors), 400

            if 'name' in validate_project_data:
                existing_project = Project.find_first(
                    name=validate_project_data['name'],
                    owner_id=current_user_id)

            if existing_project:
                return dict(
                    status='fail',
                    message=f'project with name {validate_project_data["name"]} already exists'), 409

            project = Project.get_by_id(project_id)

            if not project:
                return dict(status='fail', message=f'Project {project_id} not found'), 404

            if not is_owner_or_admin(project, current_user_id, current_user_roles):
                return dict(status='fail', message='unauthorised'), 403

            updated = Project.update(project, **validate_project_data)

            if not updated:
                return dict(status='fail', message='internal sserver error'), 500

            return dict(status='success', message=f'project {project_id} updated successfully'), 200
        except Exception as e:
            return dict(status='fail', message=str(e)), 500


class UserProjectsView(Resource):

    @jwt_required
    def get(self, user_id):
        """
        """

        current_user_id = get_jwt_identity()
        current_user_roles = get_jwt_claims()['roles']

        if not is_current_or_admin(user_id, current_user_id, current_user_roles):
            return dict(status='fail', message='unauthorised'), 403

        project_schema = ProjectSchema(many=True)
        user = User.get_by_id(user_id)

        if not user:
            return dict(status='fail', message=f'user {user_id} not found'), 404

        projects = user.projects

        projects_json, errors = project_schema.dumps(projects)

        if errors:
            return dict(status='fail', message='Internal server error'), 500

        return dict(status='success', data=dict(projects=json.loads(projects_json))), 200
