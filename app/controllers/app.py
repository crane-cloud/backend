import json
from urllib.parse import urlsplit
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
            app_name = validated_app_data['name']
            app_image = validated_app_data['image']
            project_id = validated_app_data['project_id']
            project = Project.get_by_id(project_id)
            replicas = 1

            if not project:
                return dict(status='fail', message=f'project {project_id} not found'), 404

            cluster = project.cluster
            namespace = project.alias

            if not cluster:
                return dict(status='fail', message="Invalid Cluster"), 500

            # check if app already exists
            app = App.find_first(**{'name': app_name})

            if app:
                return dict(status='fail', message=f'app {app_name} already exists'), 409


            # create the app
            new_app = App(name=app_name, image=app_image, project_id=project_id)
 

            # create deployment
            dep_name = f'{app_name}-deployment'

            # pod template
            container = client.V1Container(
                name=app_name,
                image=app_image,
                ports=[client.V1ContainerPort(container_port=80)]
            )

            # spec
            template = client.V1PodTemplateSpec(
                metadata=client.V1ObjectMeta(labels={
                    'app': app_name
                }),
                spec=client.V1PodSpec(containers=[container])
            )
            
            # spec of deployment
            spec = client.V1DeploymentSpec(
                replicas=replicas,
                template=template,
                selector={'matchLabels': {'app': app_name}}
            )

            # Instantiate the deployment
            deployment = client.V1Deployment(
                api_version="apps/v1",
                kind="Deployment",
                metadata=client.V1ObjectMeta(name=dep_name),
                spec=spec
            )

            # create deployment in  cluster
            kube_host = cluster.host
            kube_token = cluster.token
            service_host = urlsplit(kube_host).hostname

            kube, extension_api, appsv1_api, api_client, batchv1_api, storageV1Api = create_kube_clients(kube_host, kube_token)

            appsv1_api.create_namespaced_deployment(
                body=deployment,
                namespace=namespace,
                _preload_content=False
                )

            # create service in the cluster
            service_name = f'{app_name}-service'

            service_meta = client.V1ObjectMeta(
                name=service_name,
                labels={'app': app_name}
                )

            service_spec = client.V1ServiceSpec(
                type='NodePort',
                ports=[client.V1ServicePort(port=3000, target_port=80)],
                selector={'app': app_name}
            )

            service = client.V1Service(
                metadata=service_meta,
                spec=service_spec)

            kube.create_namespaced_service(
                namespace=namespace,
                body=service,
                _preload_content=False
            )

            service = kube.read_namespaced_service(name=service_name, namespace=namespace)
            service_port = service.spec.ports[0].node_port

            service_url = f'http://{service_host}:{service_port}'

            new_app.url = service_url

            saved = new_app.save()

            if not saved:
                return dict(status='fail', message='Internal Server Error'), 500

            new_app_data, _ = app_schema.dump(new_app)

            return dict(status='success', data=dict(app=new_app_data)), 201

        except client.rest.ApiException as e:
            return dict(status='fail', message=json.loads(e.body)), 500

        except Exception as e:
            return dict(status='fail', message=str(e)), 500

