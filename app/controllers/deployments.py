import json, yaml, base64, logging, json
from flask_restful import Resource, request
from kubernetes import client, config, utils

from app.schemas import DeploymentSchema

from app.helpers.kube import extension_api, kube, appsv1_api, api_client


class DeploymentsView(Resource):

    def post(self):
        """
        """

        dep_schema = DeploymentSchema(partial=True)

        deployment_data = request.get_json()

        validated_dep_data, errors = dep_schema.load(deployment_data)

        if errors:
            return dict(status='fail', message=errors), 400

        try:

            if 'yaml_file' in validated_dep_data:
                dep_yml = yaml.safe_load(
                    base64.b64decode(validated_dep_data['yaml_file'])
                    )
                namespace = validated_dep_data.get('namespace', None)

                resp = extension_api.create_namespaced_deployment(
                    body=dep_yml, namespace=namespace, _preload_content=False
                )

            else:
                name = validated_dep_data.get('name', None)
                image = validated_dep_data.get('image', None)
                port = validated_dep_data.get('port', None)
                replicas = validated_dep_data.get('replicas', None)
                kind = validated_dep_data.get('kind', None)
                namespace = validated_dep_data.get('namespace', None)

                app = name
                dep_name = '{}-deployment'.format(name)

                # Configureate Pod template container
                container = client.V1Container(
                    name=name,
                    image=image,
                    ports=[client.V1ContainerPort(container_port=80)])
                # Create and configurate a spec section
                template = client.V1PodTemplateSpec(
                    metadata=client.V1ObjectMeta(labels={"app": app}),
                    spec=client.V1PodSpec(containers=[container]))
                # Create the specification of deployment
                spec = client.V1DeploymentSpec(
                    replicas=replicas,
                    template=template,
                    selector={'matchLabels': {'app': app}})
                # Instantiate the deployment object
                deployment = client.V1Deployment(
                    api_version="apps/v1",
                    kind=kind,
                    metadata=client.V1ObjectMeta(name=dep_name),
                    spec=spec)

                resp = appsv1_api.create_namespaced_deployment(
                    body=deployment,
                    namespace=namespace,
                    _preload_content=False
                    )
                return dict(
                    status='success',
                    data=dict(deployment=json.loads(resp.read()))), 201

        except client.rest.ApiException as e:
            logging.exception(e)
            return dict(status='fail', message=json.loads(e.body)), 500
