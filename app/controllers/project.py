import json
from flask_restful import Resource, request
from kubernetes import client
from app.schemas import ProjectSchema
from app.models.project import Project
from app.models.clusters import Cluster
from app.models.user import User
from app.helpers.kube import create_kube_clients


class ProjectsView(Resource):

    def post(self):
        """
        """

        project_schema = ProjectSchema()

        project_data = request.get_json()

        validated_project_data, errors = project_schema.load(project_data)

        if errors:
            return dict(status='fail', message=errors), 400

        try:
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
            cluster_namespace = "to be reinstated"
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

    def get(self):
        """
        """
        project_schema = ProjectSchema(many=True)

        projects = Project.find_all()

        project_data, errors = project_schema.dumps(projects)

        if errors:
            return dict(status='fail', message=errors), 500

        return dict(status='success', data=dict(projects=json.loads(project_data))), 200


class ProjectDetailView(Resource):

    def get(self, project_id):
        """
        """
        project_schema = ProjectSchema()

        project = Project.get_by_id(project_id)

        if not project:
            return dict(status='fail', message=f'project {project_id} not found'), 404

        project_data, errors = project_schema.dumps(project)

        if errors:
            return dict(status='fail', message=errors), 500

        return dict(status='success', data=dict(
            project=json.loads(project_data))), 200

    def delete(self, project_id):
        """
        """

        try:
            project = Project.get_by_id(project_id)

            if not project:
                return dict(status='fail', message=f'project {project_id} not found'), 404

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

    def patch(self, project_id):
        """
        """

        try:
            project_schema = ProjectSchema(only=("name",))

            project_data = request.get_json()

            validate_project_data, errors = project_schema.load(project_data)

            if errors:
                return dict(status='fail', message=errors), 400

            project = Project.get_by_id(project_id)

            if not project:
                return dict(status='fail', message=f'Project {project_id} not found'), 404

            updated = Project.update(project, **validate_project_data)

            if not updated:
                return dict(status='fail', message='internal sserver error'), 500

            return dict(status='success', message=f'project {project_id} updated successfully'), 200
        except Exception as e:
            return dict(status='fail', message=str(e)), 500


class UserProjectsView(Resource):

    def get(self, user_id):
        """
        """

        project_schema = ProjectSchema(many=True)
        user = User.get_by_id(user_id)

        if not user:
            return dict(status='fail', message=f'user {user_id} not found'), 404

        projects = user.projects

        projects_json, errors = project_schema.dumps(projects)

        if errors:
            return dict(status='fail', message='Internal server error'), 500

        return dict(status='success', data=dict(projects=json.loads(projects_json))), 200
