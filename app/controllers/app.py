import json
from urllib.parse import urlsplit
import base64
from flask_restful import Resource, request
from kubernetes import client
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt_claims
from app.models.app import App
from app.models.project import Project
from app.helpers.kube import create_kube_clients
from app.schemas import AppSchema
from app.helpers.admin import is_owner_or_admin
from app.helpers.decorators import admin_required
from app.helpers.alias import create_alias
from app.helpers.secret_generator import generate_password, generate_db_uri
from app.helpers.connectivity import is_database_ready


class AppsView(Resource):

    @admin_required
    def post(self):
        """
        """

        app_schema = AppSchema()

        app_data = request.get_json()

        validated_app_data, errors = app_schema.load(app_data)

        # check for existing app based on name and project_id
        existing_app = App.find_first(
            name=validated_app_data['name'],
            project_id=validated_app_data['project_id'])

        if existing_app:
            return dict(
                status='fail',
                message=f'App with name {validated_app_data["name"]} already exists'
            ), 409

        if errors:
            return dict(status='fail', message=errors), 400

        validated_app_data['port'] = validated_app_data.get('port', 80)

        try:
            app_name = validated_app_data['name']
            app_alias = create_alias(validated_app_data['name'])
            app_image = validated_app_data['image']
            command = validated_app_data.get('command', None)
            need_db = validated_app_data.get('need_db', False)
            project_id = validated_app_data['project_id']
            # env_vars = validated_app_data['env_vars']
            env_vars = validated_app_data.get('env_vars', None)
            private_repo = validated_app_data.get('private_image', False)
            docker_server = validated_app_data.get('docker_server', None)
            docker_username = validated_app_data.get('docker_username', None)
            docker_password = validated_app_data.get('docker_password', None)
            docker_email = validated_app_data.get('docker_email', None)
            project = Project.get_by_id(project_id)
            replicas = 1
            app_port = validated_app_data['port']
            DATABASE_URI = None
            image_pull_secret = None

            command = command.split() if command else None

            if not project:
                return dict(status='fail', message=f'Project {project_id} not found'), 404

            cluster = project.cluster
            namespace = project.alias

            if not cluster:
                return dict(status='fail', message="Invalid Cluster"), 500

            # check if app already exists
            app = App.find_first(**{'name': app_name})

            if app:
                return dict(status='fail', message=f'App {app_name} already exists'), 409

            kube_host = cluster.host
            kube_token = cluster.token
            service_host = urlsplit(kube_host).hostname

            kube, extension_api, appsv1_api, api_client, batchv1_api, storageV1Api = create_kube_clients(kube_host, kube_token)

            # create the app
            new_app = App(name=app_name, image=app_image, project_id=project_id, alias=app_alias, port=app_port)

            if need_db:

                # create postgres pvc meta and spec
                pvc_name = f'{app_alias}-psql-pvc'
                pvc_meta = client.V1ObjectMeta(name=pvc_name)

                access_modes = ['ReadWriteOnce']
                storage_class = 'openebs-standard'
                resources = client.V1ResourceRequirements(requests=dict(storage='1Gi'))

                pvc_spec = client.V1PersistentVolumeClaimSpec(
                    access_modes=access_modes, resources=resources, storage_class_name=storage_class)

                # create postgres deployment
                pg_app_name = f'{app_alias}-postgres-db'

                # pg vars
                POSTGRES_PASSWORD = generate_password(10)
                POSTGRES_USER = app_name
                POSTGRES_DB = app_name

                DATABASE_URI = generate_db_uri(pg_app_name, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB)

                pg_env = [
                    client.V1EnvVar(name='POSTGRES_PASSWORD', value=POSTGRES_PASSWORD),
                    client.V1EnvVar(name='POSTGRES_USER', value=POSTGRES_USER),
                    client.V1EnvVar(name='POSTGRES_DB', value=POSTGRES_DB)
                ]
                pg_container = client.V1Container(
                    name=pg_app_name,
                    image='postgres:10.8-alpine',
                    ports=[client.V1ContainerPort(container_port=5432)],
                    env=pg_env
                )

                pg_template = client.V1PodTemplateSpec(
                    metadata=client.V1ObjectMeta(labels={
                        'app': pg_app_name
                    }),
                    spec=client.V1PodSpec(containers=[pg_container])

                )

                pg_spec = client.V1DeploymentSpec(
                    replicas=1,
                    template=pg_template,
                    selector={'matchLabels': {'app': pg_app_name}}
                )

                pg_deployment = client.V1Deployment(
                    api_version="apps/v1",
                    kind="Deployment",
                    metadata=client.V1ObjectMeta(name=pg_app_name),
                    spec=pg_spec
                )

                # postgres deployment
                appsv1_api.create_namespaced_deployment(
                    body=pg_deployment,
                    namespace=namespace,
                    _preload_content=False
                )

                # postgres service
                pg_service_meta = client.V1ObjectMeta(
                    name=pg_app_name,
                    labels={'app': pg_app_name}
                )

                pg_service_spec = client.V1ServiceSpec(
                    type='NodePort',
                    ports=[client.V1ServicePort(port=5432, target_port=5432)],
                    selector={'app': pg_app_name}
                )

                pg_service = client.V1Service(
                    metadata=pg_service_meta,
                    spec=pg_service_spec
                )

                kube.create_namespaced_service(
                    namespace=namespace,
                    body=pg_service,
                    _preload_content=False
                )

                # get pg_service port
                pg_service_created = kube.read_namespaced_service(name=pg_app_name, namespace=namespace)
                pg_service_port = pg_service_created.spec.ports[0].node_port

                # hold here till pg is ready
                if not is_database_ready(service_host, pg_service_port, 20):
                    return dict(status='fail', message='Failed at Database creation'), 500

            if private_repo:
                # create image pull secrets
                authstring = base64.b64encode(
                    f'{docker_username}:{docker_password}'.encode("utf-8"))

                secret_dict = dict(auths={
                    docker_server: {
                        "username": docker_username,
                        "password": docker_password,
                        "email": docker_email,
                        "auth": str(authstring, "utf-8")
                    }
                })

                secret_b64 = base64.b64encode(json.dumps(secret_dict).encode("utf-8"))

                secret_body = client.V1Secret(
                    metadata=client.V1ObjectMeta(name=app_alias),
                    type='kubernetes.io/dockerconfigjson',
                    data={'.dockerconfigjson': str(secret_b64, "utf-8")})

                kube.create_namespaced_secret(
                    namespace=namespace,
                    body=secret_body,
                    _preload_content=False)

                image_pull_secret = client.V1LocalObjectReference(name=app_alias)

            # create deployment
            dep_name = f'{app_alias}-deployment'

            # EnvVar
            env = []

            if DATABASE_URI:
                env.append(client.V1EnvVar(
                    name='DATABASE_URI', value=DATABASE_URI
                ))

            if env_vars:
                for key, value in env_vars.items():
                    env.append(client.V1EnvVar(
                        name=str(key), value=str(value)
                    ))

            # pod template
            container = client.V1Container(
                name=app_alias,
                image=app_image,
                ports=[client.V1ContainerPort(container_port=app_port)],
                env=env,
                command=command
            )

            # spec
            template = client.V1PodTemplateSpec(
                metadata=client.V1ObjectMeta(labels={
                    'app': app_alias
                }),
                spec=client.V1PodSpec(
                    containers=[container],
                    image_pull_secrets=[image_pull_secret]
                    )
            )

            # spec of deployment
            spec = client.V1DeploymentSpec(
                replicas=replicas,
                template=template,
                selector={'matchLabels': {'app': app_alias}}
            )

            # Instantiate the deployment
            deployment = client.V1Deployment(
                api_version="apps/v1",
                kind="Deployment",
                metadata=client.V1ObjectMeta(name=dep_name),
                spec=spec
            )

            # app deployment
            appsv1_api.create_namespaced_deployment(
                body=deployment,
                namespace=namespace,
                _preload_content=False
                )

            # create service in the cluster
            service_name = f'{app_alias}-service'

            service_meta = client.V1ObjectMeta(
                name=service_name,
                labels={'app': app_alias}
                )

            service_spec = client.V1ServiceSpec(
                type='NodePort',
                ports=[client.V1ServicePort(port=3000, target_port=app_port)],
                selector={'app': app_alias}
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


class ProjectAppsView(Resource):

    @jwt_required
    def post(self, project_id):
        """
        """

        current_user_id = get_jwt_identity()
        current_user_roles = get_jwt_claims()['roles']

        app_schema = AppSchema()

        app_data = request.get_json()

        validated_app_data, errors = app_schema.load(app_data)

        if errors:
            return dict(status='fail', message=errors), 400

        existing_app = App.find_first(
            name=validated_app_data['name'],
            project_id=project_id)

        if existing_app:
            return dict(
                status='fail',
                message=f'App with name {validated_app_data["name"]} already exists'
            ), 409

        validated_app_data['port'] = validated_app_data.get('port', 80)

        try:
            app_name = validated_app_data['name']
            app_alias = create_alias(validated_app_data['name'])
            app_image = validated_app_data['image']
            command = validated_app_data.get('command', None)
            need_db = validated_app_data.get('need_db', True)
            env_vars = validated_app_data['env_vars']
            private_repo = validated_app_data.get('private_image', False)
            docker_server = validated_app_data.get('docker_server', None)
            docker_username = validated_app_data.get('docker_username', None)
            docker_password = validated_app_data.get('docker_password', None)
            docker_email = validated_app_data.get('docker_email', None)
            project = Project.get_by_id(project_id)
            replicas = 1
            app_port = validated_app_data['port']
            DATABASE_URI = None
            image_pull_secret = None


            command = command.split() if command else None

            if not project:
                return dict(status='fail', message=f'project {project_id} not found'), 404

            if not is_owner_or_admin(project, current_user_id, current_user_roles):
                return dict(status='fail', message='Unauthorised'), 403

            cluster = project.cluster
            namespace = project.alias

            if not cluster:
                return dict(status='fail', message="Invalid Cluster"), 500

            # check if app already exists
            app = App.find_first(**{'name': app_name})

            if app:
                return dict(status='fail', message=f'App {app_name} already exists'), 409

            kube_host = cluster.host
            kube_token = cluster.token
            service_host = urlsplit(kube_host).hostname

            kube, extension_api, appsv1_api, api_client, batchv1_api, storageV1Api = create_kube_clients(kube_host, kube_token)

            # create the app
            new_app = App(name=app_name, image=app_image, project_id=project_id, alias=app_alias, port=app_port)

            if need_db:

                # create postgres pvc meta and spec
                pvc_name = f'{app_alias}-psql-pvc'
                pvc_meta = client.V1ObjectMeta(name=pvc_name)

                access_modes = ['ReadWriteOnce']
                storage_class = 'openebs-standard'
                resources = client.V1ResourceRequirements(requests=dict(storage='1Gi'))

                pvc_spec = client.V1PersistentVolumeClaimSpec(
                    access_modes=access_modes, resources=resources, storage_class_name=storage_class)

                # create postgres deployment
                pg_app_name = f'{app_alias}-postgres-db'

                # pg vars
                POSTGRES_PASSWORD = generate_password(10)
                POSTGRES_USER = app_name
                POSTGRES_DB = app_name

                DATABASE_URI = generate_db_uri(pg_app_name, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB)

                pg_env = [
                    client.V1EnvVar(name='POSTGRES_PASSWORD', value=POSTGRES_PASSWORD),
                    client.V1EnvVar(name='POSTGRES_USER', value=POSTGRES_USER),
                    client.V1EnvVar(name='POSTGRES_DB', value=POSTGRES_DB)
                ]
                pg_container = client.V1Container(
                    name=pg_app_name,
                    image='postgres:10.8-alpine',
                    ports=[client.V1ContainerPort(container_port=5432)],
                    env=pg_env
                )

                pg_template = client.V1PodTemplateSpec(
                    metadata=client.V1ObjectMeta(labels={
                        'app': pg_app_name
                    }),
                    spec=client.V1PodSpec(containers=[pg_container])

                )

                pg_spec = client.V1DeploymentSpec(
                    replicas=1,
                    template=pg_template,
                    selector={'matchLabels': {'app': pg_app_name}}
                )

                pg_deployment = client.V1Deployment(
                    api_version="apps/v1",
                    kind="Deployment",
                    metadata=client.V1ObjectMeta(name=pg_app_name),
                    spec=pg_spec
                )

                # postgres deployment
                appsv1_api.create_namespaced_deployment(
                    body=pg_deployment,
                    namespace=namespace,
                    _preload_content=False
                )

                # postgres service
                pg_service_meta = client.V1ObjectMeta(
                    name=pg_app_name,
                    labels={'app': pg_app_name}
                )

                pg_service_spec = client.V1ServiceSpec(
                    type='NodePort',
                    ports=[client.V1ServicePort(port=5432, target_port=5432)],
                    selector={'app': pg_app_name}
                )

                pg_service = client.V1Service(
                    metadata=pg_service_meta,
                    spec=pg_service_spec
                )

                kube.create_namespaced_service(
                    namespace=namespace,
                    body=pg_service,
                    _preload_content=False
                )

                # get pg_service port
                pg_service_created = kube.read_namespaced_service(name=pg_app_name, namespace=namespace)
                pg_service_port = pg_service_created.spec.ports[0].node_port

                # hold here till pg is ready
                if not is_database_ready(service_host, pg_service_port, 20):
                    return dict(status='fail', message='Failed at Database creation'), 500

            if private_repo:
                # create image pull secrets
                authstring = base64.b64encode(
                    f'{docker_username}:{docker_password}'.encode("utf-8"))

                secret_dict = dict(auths={
                    docker_server: {
                        "username": docker_username,
                        "password": docker_password,
                        "email": docker_email,
                        "auth": str(authstring, "utf-8")
                    }
                })

                secret_b64 = base64.b64encode(json.dumps(secret_dict).encode("utf-8"))

                secret_body = client.V1Secret(
                    metadata=client.V1ObjectMeta(name=app_alias),
                    type='kubernetes.io/dockerconfigjson',
                    data={'.dockerconfigjson': str(secret_b64, "utf-8")})

                kube.create_namespaced_secret(
                    namespace=namespace,
                    body=secret_body,
                    _preload_content=False)
                
                image_pull_secret = client.V1LocalObjectReference(name=app_alias)

            # create deployment
            dep_name = f'{app_alias}-deployment'

            # EnvVar
            env = []

            if DATABASE_URI:
                env.append(client.V1EnvVar(
                    name='DATABASE_URI', value=DATABASE_URI
                ))

            if env_vars:
                for key, value in env_vars.items():
                    env.append(client.V1EnvVar(
                        name=str(key), value=str(value)
                    ))

            # pod template
            container = client.V1Container(
                name=app_alias,
                image=app_image,
                ports=[client.V1ContainerPort(container_port=app_port)],
                env=env,
                command=command
                )

            # spec
            template = client.V1PodTemplateSpec(
                metadata=client.V1ObjectMeta(labels={
                    'app': app_alias
                }),
                spec=client.V1PodSpec(
                    containers=[container],
                    image_pull_secrets=[image_pull_secret]
                    )
            )

            # spec of deployment
            spec = client.V1DeploymentSpec(
                replicas=replicas,
                template=template,
                selector={'matchLabels': {'app': app_alias}}
            )

            # Instantiate the deployment
            deployment = client.V1Deployment(
                api_version="apps/v1",
                kind="Deployment",
                metadata=client.V1ObjectMeta(name=dep_name),
                spec=spec
            )

            # create deployment in  cluster

            appsv1_api.create_namespaced_deployment(
                body=deployment,
                namespace=namespace,
                _preload_content=False
                )

            # create service in the cluster
            service_name = f'{app_alias}-service'

            service_meta = client.V1ObjectMeta(
                name=service_name,
                labels={'app': app_alias}
                )

            service_spec = client.V1ServiceSpec(
                type='NodePort',
                ports=[client.V1ServicePort(port=3000, target_port=app_port)],
                selector={'app': app_alias}
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

    @jwt_required
    def get(self, project_id):
        """
        """

        current_user_id = get_jwt_identity()
        current_user_roles = get_jwt_claims()['roles']

        app_schema = AppSchema(many=True)

        project = Project.get_by_id(project_id)

        if not project:
            return dict(status='fail', message=f'project {project_id} not found'), 404

        if not is_owner_or_admin(project, current_user_id, current_user_roles):
            return dict(status='fail', message='Unauthorised'), 403

        apps = App.find_all(project_id=project_id)

        apps_data, errors = app_schema.dumps(apps)

        if errors:
            return dict(status='fail', message=errors), 500

        return dict(status='success', data=dict(apps=json.loads(apps_data))), 200


class AppDetailView(Resource):

    @jwt_required
    def get(self, app_id):
        """
        """

        current_user_id = get_jwt_identity()
        current_user_roles = get_jwt_claims()['roles']

        app_schema = AppSchema()

        app = App.get_by_id(app_id)

        if not app:
            return dict(status='fail', message=f'App {app_id} not found'), 404

        project = app.project

        if not project:
            return dict(status='fail', message='Internal server error'), 500

        if not is_owner_or_admin(project, current_user_id, current_user_roles):
            return dict(status='fail', message='Unauthorised'), 403

        app_data, errors = app_schema.dumps(app)

        if errors:
            return dict(status='fail', message=errors), 500

        return dict(status='success', data=dict(apps=json.loads(app_data))), 200

    @jwt_required
    def delete(self, app_id):
        """
        """

        try:

            current_user_id = get_jwt_identity()
            current_user_roles = get_jwt_claims()['roles']

            app = App.get_by_id(app_id)

            if not app:
                return dict(status='fail', message=f'app {app_id} not found'), 404

            project = app.project

            if not project:
                return dict(status='fail', message='Internal server error'), 500

            if not is_owner_or_admin(project, current_user_id, current_user_roles):
                return dict(status='fail', message='Unauthorised'), 403

            cluster = project.cluster
            namespace = project.alias

            if not cluster or not namespace:
                return dict(status='fail', message='Internal server error'), 500

            kube_host = cluster.host
            kube_token = cluster.token

            kube, extension_api, appsv1_api, api_client, batchv1_api, \
                storageV1Api = create_kube_clients(kube_host, kube_token)

            # delete deployment and service for the app
            deployment_name = f'{app.alias}-deployment'
            service_name = f'{app.alias}-service'
            deployment = appsv1_api.read_namespaced_deployment(name=deployment_name, namespace=namespace)

            if deployment:
                appsv1_api.delete_namespaced_deployment(name=deployment_name, namespace=namespace)

            service = kube.read_namespaced_service(name=service_name, namespace=namespace)

            if service:
                kube.delete_namespaced_service(name=service_name, namespace=namespace)

            # delete the app from the database
            deleted = app.delete()

            if not deleted:
                return dict(status='fail', message='Internal server error'), 500

            return dict(status='success', message=f'App {app_id} deleted successfully'), 200

        except client.rest.ApiException as e:
            return dict(status='fail', message=json.loads(e.body)), 500

        except Exception as e:
            return dict(status='fail', message=str(e)), 500
