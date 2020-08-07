import json
from urllib.parse import urlsplit
import base64
import datetime
from flask_restful import Resource, request
from kubernetes import client
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt_claims
from app.models.app import App
from app.models.project import Project
from app.helpers.kube import create_kube_clients
from app.schemas import AppSchema, MetricsSchema
from app.helpers.admin import is_owner_or_admin
from app.helpers.decorators import admin_required
from app.helpers.alias import create_alias
from app.helpers.secret_generator import generate_password, generate_db_uri
from app.helpers.connectivity import is_database_ready
from app.models.clusters import Cluster
from app.helpers.clean_up import resource_clean_up
from app.helpers.db_flavor import db_flavors
from app.helpers.prometheus import prometheus


class AppsView(Resource):

    @admin_required
    def post(self):
        """
        """

        resource_registry = {
            'db_deployment': False,
            'db_service': False,
            'image_pull_secret': False,
            'app_deployment': False,
            'app_service': False
        }

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
        db_user = validated_app_data.get('db_user', None)
        db_password = validated_app_data.get('db_password', None)
        db_name = validated_app_data.get('db_name', None)
        db_flavor = validated_app_data.get('db_flavor', 'postgres')
        replicas = validated_app_data.get('replicas', 1)
        app_port = validated_app_data.get('port')
        DATABASE_URI = None
        image_pull_secret = None
        DB_HOST = ""
        DB_USER = ""
        DB_PASSWORD = ""
        DB_DATABASE = ""
        DB_PORT = ""

        command = command.split() if command else None

        project = Project.get_by_id(project_id)

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

        kube_client = create_kube_clients(kube_host, kube_token)

        try:

            # create the app
            new_app = App(
                name=app_name,
                image=app_image,
                project_id=project_id,
                alias=app_alias,
                port=app_port
                )

            if need_db:

                if db_flavor not in db_flavors:
                    return dict(
                        status='fail',
                        message='Unsupported database flavor'
                        ), 400

                # create postgres pvc meta and spec
                pvc_name = f'{app_alias}-db-pvc'
                pvc_meta = client.V1ObjectMeta(name=pvc_name)

                access_modes = ['ReadWriteOnce']
                storage_class = 'openebs-standard'
                resources = client.V1ResourceRequirements(requests=dict(storage='1Gi'))

                pvc_spec = client.V1PersistentVolumeClaimSpec(
                    access_modes=access_modes, resources=resources, storage_class_name=storage_class)

                db_app_name = f'{app_alias}-{db_flavor}-db'

                db_image = db_flavors[db_flavor]['image']
                db_port = db_flavors[db_flavor]['port']

                # Declare Database connection variables
                DB_HOST = db_app_name
                DB_USER = db_user if db_user else app_name
                DB_PASSWORD = db_password if db_password else generate_password(10)
                DB_DATABASE = db_name if db_name else app_name
                DB_PORT = db_port

                if db_flavor in ['mysql', 'mariadb']:
                    MYSQL_ROOT_PASSWORD = generate_password(10)

                    db_env = [
                        client.V1EnvVar(name='MYSQL_ROOT_PASSWORD', value=MYSQL_ROOT_PASSWORD),
                        client.V1EnvVar(name='MYSQL_DATABASE', value=DB_DATABASE),
                        client.V1EnvVar(name='MYSQL_USER', value=DB_USER),
                        client.V1EnvVar(name='MYSQL_PASSWORD', value=DB_PASSWORD)
                    ]

                if db_flavor == 'postgres':

                    DATABASE_URI = generate_db_uri(DB_HOST, DB_USER, DB_PASSWORD, DB_DATABASE)

                    db_env = [
                        client.V1EnvVar(name='POSTGRES_PASSWORD', value=DB_PASSWORD),
                        client.V1EnvVar(name='POSTGRES_USER', value=DB_USER),
                        client.V1EnvVar(name='POSTGRES_DB', value=DB_DATABASE)
                    ]

                db_container = client.V1Container(
                    name=db_app_name,
                    image=db_image,
                    ports=[client.V1ContainerPort(container_port=db_port)],
                    env=db_env
                )

                db_template = client.V1PodTemplateSpec(
                    metadata=client.V1ObjectMeta(labels={
                        'app': db_app_name
                    }),
                    spec=client.V1PodSpec(containers=[db_container])

                )

                db_spec = client.V1DeploymentSpec(
                    replicas=1,
                    template=db_template,
                    selector={'matchLabels': {'app': db_app_name}}
                )

                db_deployment = client.V1Deployment(
                    api_version="apps/v1",
                    kind="Deployment",
                    metadata=client.V1ObjectMeta(name=db_app_name),
                    spec=db_spec
                )

                # postgres deployment
                kube_client.appsv1_api.create_namespaced_deployment(
                    body=db_deployment,
                    namespace=namespace,
                    _preload_content=False
                )

                # update resource registry
                resource_registry['db_deployment'] = True

                # postgres service
                db_service_meta = client.V1ObjectMeta(
                    name=db_app_name,
                    labels={'app': db_app_name}
                )

                db_service_spec = client.V1ServiceSpec(
                    type='NodePort',
                    ports=[client.V1ServicePort(port=db_port, target_port=db_port)],
                    selector={'app': db_app_name}
                )

                db_service = client.V1Service(
                    metadata=db_service_meta,
                    spec=db_service_spec
                )

                kube_client.kube.create_namespaced_service(
                    namespace=namespace,
                    body=db_service,
                    _preload_content=False
                )

                # Update resource registry
                resource_registry['db_service'] = True

                # get pg_service port
                db_service_created = kube_client.kube.read_namespaced_service(name=db_app_name, namespace=namespace)
                db_service_port = db_service_created.spec.ports[0].node_port

                # hold here till pg is ready
                if not is_database_ready(service_host, db_service_port, 20):
                    return dict(status='fail', message='Failed at Database creation'), 500

            if private_repo:

                # handle gcr credentials
                if 'gcr' in docker_server and docker_username == '_json_key':
                    docker_password = json.dumps(json.loads(base64.b64decode(docker_password)))

                # create image pull secrets
                authstring = base64.b64encode(
                    f'{docker_username}:{docker_password}'.encode("utf-8"))

                secret_dict = dict(auths={
                    docker_server: {
                        "username": docker_username,
                        "password": str(docker_password),
                        "email": docker_email,
                        "auth": str(authstring, "utf-8")
                    }
                })

                secret_b64 = base64.b64encode(json.dumps(secret_dict).encode("utf-8"))

                secret_body = client.V1Secret(
                    metadata=client.V1ObjectMeta(name=app_alias),
                    type='kubernetes.io/dockerconfigjson',
                    data={'.dockerconfigjson': str(secret_b64, "utf-8")})

                kube_client.kube.create_namespaced_secret(
                    namespace=namespace,
                    body=secret_body,
                    _preload_content=False)

                # update registry
                resource_registry['image_pull_secret'] = True

                image_pull_secret = client.V1LocalObjectReference(
                    name=app_alias)

            # create deployment
            dep_name = f'{app_alias}-deployment'

            # EnvVar
            if DB_HOST or DB_USER or DB_PASSWORD or DB_PORT or DB_DATABASE:
                env = [
                    client.V1EnvVar(name='DB_HOST', value=DB_HOST),
                    client.V1EnvVar(name='DB_USER', value=DB_USER),
                    client.V1EnvVar(name='DB_PASSWORD', value=DB_PASSWORD),
                    client.V1EnvVar(name='DB_PORT', value=str(DB_PORT)),
                    client.V1EnvVar(name='DB_DATABASE', value=DB_DATABASE)
                ]
            else:
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
            kube_client.appsv1_api.create_namespaced_deployment(
                body=deployment,
                namespace=namespace,
                _preload_content=False
                )

            # update registry
            resource_registry['app_deployment'] = True

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

            kube_client.kube.create_namespaced_service(
                namespace=namespace,
                body=service,
                _preload_content=False
            )

            # update resource registry
            resource_registry['app_service'] = True

            service = kube_client.kube.read_namespaced_service(name=service_name, namespace=namespace)
            service_port = service.spec.ports[0].node_port

            service_url = f'http://{service_host}:{service_port}'

            new_app.url = service_url

            saved = new_app.save()

            if not saved:
                return dict(status='fail', message='Internal Server Error'), 500

            new_app_data, _ = app_schema.dump(new_app)

            return dict(status='success', data=dict(app=new_app_data)), 201

        except client.rest.ApiException as e:
            resource_clean_up(
                resource_registry,
                app_alias,
                namespace,
                kube_client
                )
            return dict(status='fail', message=json.loads(e.body)), 500

        except Exception as e:
            resource_clean_up(
                resource_registry,
                app_alias,
                namespace,
                kube_client
                )
            return dict(status='fail', message=str(e)), 500


class ProjectAppsView(Resource):

    @jwt_required
    def post(self, project_id):
        """
        """

        resource_registry = {
            'db_deployment': False,
            'db_service': False,
            'image_pull_secret': False,
            'app_deployment': False,
            'app_service': False
        }

        current_user_id = get_jwt_identity()
        current_user_roles = get_jwt_claims()['roles']

        app_schema = AppSchema()

        app_data = request.get_json()

        validated_app_data, errors = app_schema.load(app_data, partial=("project_id",))

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

        app_name = validated_app_data['name']
        app_alias = create_alias(validated_app_data['name'])
        app_image = validated_app_data['image']
        command = validated_app_data.get('command', None)
        need_db = validated_app_data.get('need_db', True)
        # env_vars = validated_app_data['env_vars']
        env_vars = validated_app_data.get('env_vars', None)
        private_repo = validated_app_data.get('private_image', False)
        docker_server = validated_app_data.get('docker_server', None)
        docker_username = validated_app_data.get('docker_username', None)
        docker_password = validated_app_data.get('docker_password', None)
        docker_email = validated_app_data.get('docker_email', None)
        db_user = validated_app_data.get('db_user', None)
        db_password = validated_app_data.get('db_password', None)
        db_name = validated_app_data.get('db_name', None)
        db_flavor = validated_app_data.get('db_flavor', 'postgres')
        replicas = validated_app_data.get('replicas', 1)
        app_port = validated_app_data.get('port', None)
        DATABASE_URI = None
        image_pull_secret = None
        DB_HOST = ""
        DB_USER = ""
        DB_PASSWORD = ""
        DB_DATABASE = ""
        DB_PORT = ""

        command = command.split() if command else None

        project = Project.get_by_id(project_id)

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
            return dict(
                status='fail',
                message=f'App {app_name} already exists'
                ), 409

        kube_host = cluster.host
        kube_token = cluster.token
        service_host = urlsplit(kube_host).hostname

        kube_client = create_kube_clients(kube_host, kube_token)

        try:

            # create the app
            new_app = App(
                name=app_name,
                image=app_image,
                project_id=project_id,
                alias=app_alias,
                port=app_port
                )

            if need_db:

                if db_flavor not in db_flavors:
                    return dict(
                        status='fail',
                        message='Unsupported database flavor'
                        ), 400

                # create postgres pvc meta and spec
                pvc_name = f'{app_alias}-db-pvc'
                pvc_meta = client.V1ObjectMeta(name=pvc_name)

                access_modes = ['ReadWriteOnce']
                storage_class = 'openebs-standard'
                resources = client.V1ResourceRequirements(requests=dict(storage='1Gi'))

                pvc_spec = client.V1PersistentVolumeClaimSpec(
                    access_modes=access_modes, resources=resources, storage_class_name=storage_class)

                db_app_name = f'{app_alias}-{db_flavor}-db'

                db_image = db_flavors[db_flavor]['image']
                db_port = db_flavors[db_flavor]['port']

                # Database connection variables
                DB_HOST = db_app_name
                DB_USER = db_user if db_user else app_name
                DB_PASSWORD = db_password if db_password else generate_password(10)
                DB_DATABASE = db_name if db_name else app_name
                DB_PORT = db_port

                if db_flavor in ['mysql', 'mariadb']:
                    MYSQL_ROOT_PASSWORD = generate_password(10)

                    db_env = [
                        client.V1EnvVar(name='MYSQL_ROOT_PASSWORD', value=MYSQL_ROOT_PASSWORD),
                        client.V1EnvVar(name='MYSQL_DATABASE', value=DB_DATABASE),
                        client.V1EnvVar(name='MYSQL_USER', value=DB_USER),
                        client.V1EnvVar(name='MYSQL_PASSWORD', value=DB_PASSWORD)
                    ]

                if db_flavor == 'postgres':
                    # pg vars
                    DB_PASSWORD = db_password if db_password else generate_password(10)
                    DB_USER = db_user if db_user else app_name
                    DB_DATABASE = db_name if db_name else app_name

                    DATABASE_URI = generate_db_uri(DB_HOST, DB_USER, DB_PASSWORD, DB_DATABASE)

                    db_env = [
                        client.V1EnvVar(name='POSTGRES_PASSWORD', value=DB_PASSWORD),
                        client.V1EnvVar(name='POSTGRES_USER', value=DB_USER),
                        client.V1EnvVar(name='POSTGRES_DB', value=DB_DATABASE)
                    ]

                db_container = client.V1Container(
                    name=db_app_name,
                    image=db_image,
                    ports=[client.V1ContainerPort(container_port=db_port)],
                    env=db_env
                )

                db_template = client.V1PodTemplateSpec(
                    metadata=client.V1ObjectMeta(labels={
                        'app': db_app_name
                    }),
                    spec=client.V1PodSpec(containers=[db_container])

                )

                db_spec = client.V1DeploymentSpec(
                    replicas=1,
                    template=db_template,
                    selector={'matchLabels': {'app': db_app_name}}
                )

                db_deployment = client.V1Deployment(
                    api_version="apps/v1",
                    kind="Deployment",
                    metadata=client.V1ObjectMeta(name=db_app_name),
                    spec=db_spec
                )

                # postgres deployment
                kube_client.appsv1_api.create_namespaced_deployment(
                    body=db_deployment,
                    namespace=namespace,
                    _preload_content=False
                )

                # update resource registry
                resource_registry['db_deployment'] = True

                # postgres service
                db_service_meta = client.V1ObjectMeta(
                    name=db_app_name,
                    labels={'app': db_app_name}
                )

                db_service_spec = client.V1ServiceSpec(
                    type='NodePort',
                    ports=[client.V1ServicePort(port=db_port, target_port=db_port)],
                    selector={'app': db_app_name}
                )

                db_service = client.V1Service(
                    metadata=db_service_meta,
                    spec=db_service_spec
                )

                kube_client.kube.create_namespaced_service(
                    namespace=namespace,
                    body=db_service,
                    _preload_content=False
                )

                # Update resource registry
                resource_registry['db_service'] = True

                # get pg_service port
                db_service_created = kube_client.kube.read_namespaced_service(name=db_app_name, namespace=namespace)
                db_service_port = db_service_created.spec.ports[0].node_port

                # hold here till pg is ready
                if not is_database_ready(service_host, db_service_port, 20):
                    return dict(status='fail', message='Failed at Database creation'), 500

            if private_repo:

                # handle gcr credentials
                if 'gcr' in docker_server and docker_username == '_json_key':
                    docker_password = json.dumps(
                        json.loads(base64.b64decode(docker_password))
                        )

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

                secret_b64 = base64.b64encode(
                    json.dumps(secret_dict).encode("utf-8")
                    )

                secret_body = client.V1Secret(
                    metadata=client.V1ObjectMeta(name=app_alias),
                    type='kubernetes.io/dockerconfigjson',
                    data={'.dockerconfigjson': str(secret_b64, "utf-8")})

                kube_client.kube.create_namespaced_secret(
                    namespace=namespace,
                    body=secret_body,
                    _preload_content=False)

                # update registry
                resource_registry['image_pull_secret'] = True

                image_pull_secret = client.V1LocalObjectReference(name=app_alias)

            # create deployment
            dep_name = f'{app_alias}-deployment'

            # EnvVar
            if DB_HOST or DB_USER or DB_PASSWORD or DB_PORT or DB_DATABASE:
                env = [
                    client.V1EnvVar(name='DB_HOST', value=DB_HOST),
                    client.V1EnvVar(name='DB_USER', value=DB_USER),
                    client.V1EnvVar(name='DB_PASSWORD', value=DB_PASSWORD),
                    client.V1EnvVar(name='DB_PORT', value=str(DB_PORT)),
                    client.V1EnvVar(name='DB_DATABASE', value=DB_DATABASE)
                ]
            else:
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

            kube_client.appsv1_api.create_namespaced_deployment(
                body=deployment,
                namespace=namespace,
                _preload_content=False
                )

            # update registry
            resource_registry['app_deployment'] = True

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

            kube_client.kube.create_namespaced_service(
                namespace=namespace,
                body=service,
                _preload_content=False
            )

            # update resource registry
            resource_registry['app_service'] = True

            service = kube_client.kube.read_namespaced_service(
                name=service_name, namespace=namespace)
            service_port = service.spec.ports[0].node_port

            service_url = f'http://{service_host}:{service_port}'

            new_app.url = service_url

            saved = new_app.save()

            if not saved:
                return dict(
                    status='fail',
                    message='Internal Server Error'
                    ), 500

            new_app_data, _ = app_schema.dump(new_app)

            return dict(status='success', data=dict(app=new_app_data)), 201

        except client.rest.ApiException as e:
            resource_clean_up(
                resource_registry,
                app_alias,
                namespace,
                kube_client
                )
            return dict(status='fail', message=json.loads(e.body)), 500

        except Exception as e:
            resource_clean_up(
                resource_registry,
                app_alias,
                namespace,
                kube_client
                )
            return dict(status='fail', message=str(e)), 500

    @jwt_required
    def get(self, project_id):
        """
        """
        try:
            current_user_id = get_jwt_identity()
            current_user_roles = get_jwt_claims()['roles']

            app_schema = AppSchema(many=True)

            project = Project.get_by_id(project_id)

            if not project:
                return dict(status='fail', message=f'project {project_id} not found'), 404

            if not is_owner_or_admin(project, current_user_id, current_user_roles):
                return dict(status='fail', message='Unauthorised'), 403

            cluster = Cluster.get_by_id(project.cluster_id)

            if not cluster:
                return dict(status='fail', message=f'cluster with id {project.cluster_id} does not exist'), 404

            kube_host = cluster.host
            kube_token = cluster.token
            kube_client = create_kube_clients(kube_host, kube_token)

            apps = App.find_all(project_id=project_id)

            apps_data, errors = app_schema.dumps(apps)

            if errors:
                return dict(status='fail', message=errors), 500

            apps_data_list = json.loads(apps_data)

            for app in apps_data_list:
                app_status_object = \
                    kube_client.appsv1_api.read_namespaced_deployment_status(
                        app['alias']+"-deployment", project.alias)

                app_deployment_status_conditions = app_status_object.status.conditions

                for deplyoment_status_condition in app_deployment_status_conditions:
                    if deplyoment_status_condition.type == "Available":
                        app_deployment_status = deplyoment_status_condition.status

                try:
                    app_db_status_object = \
                        kube_client.appsv1_api.read_namespaced_deployment_status(
                            app['alias']+"-postgres-db", project.alias)

                    app_db_state_conditions = app_db_status_object.status.conditions

                    for app_db_condition in app_db_state_conditions:
                        if app_db_condition.type == "Available":
                            app_db_status = app_db_condition.status

                except client.rest.ApiException:
                    app_db_status = None

                if app_deployment_status and not app_db_status:
                    if app_deployment_status == "True":
                        app['app_running_status'] = "running"
                    else:
                        app['app_running_status'] = "failed"
                elif app_deployment_status and app_db_status:
                    if app_deployment_status == "True" and app_db_status == "True":
                        app['app_running_status'] = "running"
                    else:
                        app['app_running_status'] = "failed"
                else:
                    app['app_running_status'] = "unknown"

            return dict(status='success', data=dict(apps=apps_data_list)), 200

        except client.rest.ApiException as exc:
            return dict(status='fail', message=exc.reason), exc.status

        except Exception as exc:
            return dict(status='fail', message=str(exc)), 500


class AppDetailView(Resource):

    @jwt_required
    def get(self, app_id):
        """
        """
        try:
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

            app_list = json.loads(app_data)

            cluster = Cluster.get_by_id(project.cluster_id)

            if not cluster:
                return dict(
                    status='fail',
                    message=f'cluster with id {project.cluster_id} does not exist'), 404

            kube_host = cluster.host
            kube_token = cluster.token
            kube_client = create_kube_clients(kube_host, kube_token)

            app_status_object = \
                kube_client.appsv1_api.read_namespaced_deployment_status(
                    app_list['alias']+"-deployment", project.alias)

            app_deployment_status_conditions = app_status_object.status.conditions

            for deplyoment_status_condition in app_deployment_status_conditions:
                if deplyoment_status_condition.type == "Available":
                    app_deployment_status = deplyoment_status_condition.status

            try:
                app_db_status_object = \
                    kube_client.appsv1_api.read_namespaced_deployment_status(
                        app_list['alias']+"-postgres-db", project.alias)

                app_db_state_conditions = app_db_status_object.status.conditions

                for app_db_condition in app_db_state_conditions:
                    if app_db_condition.type == "Available":
                        app_db_status = app_db_condition.status

            except client.rest.ApiException:
                app_db_status = None

            if app_deployment_status and not app_db_status:
                if app_deployment_status == "True":
                    app_list['app_running_status'] = "running"
                else:
                    app_list['app_running_status'] = "failed"
            elif app_deployment_status and app_db_status:
                if app_deployment_status == "True" and app_db_status == "True":
                    app_list['app_running_status'] = "running"
                else:
                    app_list['app_running_status'] = "failed"
            else:
                app_list['app_running_status'] = "unknown"

            return dict(status='success', data=dict(apps=app_list)), 200

        except client.rest.ApiException as exc:
            return dict(status='fail', message=exc.reason), exc.status

        except Exception as exc:
            return dict(status='fail', message=str(exc)), 500

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

            kube_client = create_kube_clients(kube_host, kube_token)

            # delete deployment and service for the app
            deployment_name = f'{app.alias}-deployment'
            service_name = f'{app.alias}-service'
            deployment = kube_client.appsv1_api.read_namespaced_deployment(
                name=deployment_name,
                namespace=namespace
                )

            if deployment:
                kube_client.appsv1_api.delete_namespaced_deployment(
                    name=deployment_name,
                    namespace=namespace
                    )

            service = kube_client.kube.read_namespaced_service(
                name=service_name,
                namespace=namespace
                )

            if service:
                kube_client.kube.delete_namespaced_service(
                    name=service_name,
                    namespace=namespace
                    )

            # delete the app from the database
            deleted = app.delete()

            if not deleted:
                return dict(status='fail', message='Internal server error'), 500

            return dict(status='success', message=f'App {app_id} deleted successfully'), 200

        except client.rest.ApiException as e:
            return dict(status='fail', message=json.loads(e.body)), 500

        except Exception as e:
            return dict(status='fail', message=str(e)), 500


class AppMemoryUsageView(Resource):

    @jwt_required
    def post(self, project_id, app_id):
        """
        """

        app_memory_schema = MetricsSchema()
        app_query_data = request.get_json()

        validated_query_data, errors = app_memory_schema.load(
            app_query_data)

        if errors:
            return dict(status='fail', message=errors), 400

        current_time = datetime.datetime.now()
        yesterday_time = current_time + datetime.timedelta(days=-1)

        start = validated_query_data.get('start', yesterday_time.timestamp())
        end = validated_query_data.get('end', current_time.timestamp())
        step = validated_query_data.get('step', '1h')

        current_user_id = get_jwt_identity()
        current_user_roles = get_jwt_claims()['roles']

        project = Project.get_by_id(project_id)

        if not project:
            return dict(
                status='fail',
                message=f'project {project_id} not found'
            ), 404

        app = App.get_by_id(app_id)

        if not app:
            return dict(status='fail', message=f'App {app_id} not found'), 404

        if not is_owner_or_admin(project, current_user_id, current_user_roles):
            return dict(status='fail', message='Unauthorised'), 403

        app_alias = app.alias
        namespace = project.alias

        prom_memory_data = prometheus.query_rang(
            start=start,
            end=end,
            step=step,
            metric='sum(rate(container_memory_usage_bytes{container_name!="POD", image!="",pod=~"'+app_alias+'.*", namespace="'+namespace+'"}[5m]))')

        new_data = json.loads(prom_memory_data)
        final_data_list = []

        for value in new_data["data"]["result"][0]["values"]:
            mem_case = {'timestamp': float(value[0]), 'value': float(value[1])}
            final_data_list.append(mem_case)

        return dict(status='success', data=dict(values=final_data_list)), 200


