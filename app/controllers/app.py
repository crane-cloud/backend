import json
from flask_restful import Resource, request
from kubernetes import client
from app.models.app import App
from app.models.project import Project
from app.helpers.kube import create_kube_clients
from app.schemas import AppSchema


class AppsView(Resource):

    def post(self):
        """
        """

        app_schema = AppSchema()

        app_data = request.get_json()

        validated_app_data, errors = app_schema.load(app_data)

        if errors:
            return dict(status='fail', message=errors), 400

        try:
            project_id = validated_app_data['project_id']
            project = Project.get_by_id(project_id)

            if not project:
                return dict(status='fail', message=f'project {project_id} not found'), 404

            cluster = project.cluster
            namespace = project.alias

            # create deployment




        except Exception as e:
            return dict(status='fail', message=str(e))

        