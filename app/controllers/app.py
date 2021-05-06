import json
from urllib.parse import urlsplit
import base64
import datetime
from flask_restful import Resource, request
from kubernetes import client
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt_claims
import datetime
from prometheus_http_client import Prometheus
from app.models.app import App
from app.models.project import Project
from app.helpers.kube import create_kube_clients
from app.schemas import AppSchema, MetricsSchema, PodsLogsSchema
from app.helpers.admin import is_owner_or_admin
from app.helpers.decorators import admin_required
from app.helpers.alias import create_alias
from app.models.clusters import Cluster
from app.helpers.clean_up import resource_clean_up
from app.helpers.prometheus import prometheus
from app.helpers.url import get_app_subdomain


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
            'app_service': False,
            'ingress_entry': False
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
        project_id = validated_app_data['project_id']
        # env_vars = validated_app_data['env_vars']
        env_vars = validated_app_data.get('env_vars', None)
        private_repo = validated_app_data.get('private_image', False)
        docker_server = validated_app_data.get('docker_server', None)
        docker_username = validated_app_data.get('docker_username', None)
        docker_password = validated_app_data.get('docker_password', None)
        docker_email = validated_app_data.get('docker_email', None)
        replicas = validated_app_data.get('replicas', 1)
        app_port = validated_app_data.get('port')
        image_pull_secret = None

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

            if private_repo:

                # handle gcr credentials
                if 'gcr' in docker_server and docker_username == '_json_key':
                    docker_password = json.dumps(
                        json.loads(base64.b64decode(docker_password)))

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

                secret_b64 = base64.b64encode(
                    json.dumps(secret_dict).encode("utf-8"))

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

            # create app deployment's pvc meta and spec
            pvc_name = f'{app_alias}-pvc'
            pvc_meta = client.V1ObjectMeta(name=pvc_name)

            access_modes = ['ReadWriteOnce']
            storage_class = 'openebs-standard'
            resources = client.V1ResourceRequirements(
                requests=dict(storage='1Gi'))

            pvc_spec = client.V1PersistentVolumeClaimSpec(
                access_modes=access_modes, resources=resources, storage_class_name=storage_class)

            # Create a PVC 
            pvc = client.V1PersistentVolumeClaim(
                api_version="v1",
                kind="PersistentVolumeClaim", 
                metadata=pvc_meta,
                spec=pvc_spec
            )

            kube_client.kube.create_namespaced_persistent_volume_claim(
                namespace=namespace,
                body=pvc
            )

            # create deployment
            dep_name = f'{app_alias}-deployment'

            # # EnvVar
            env = []
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
                command=command,
                volume_mounts=[client.V1VolumeMount(mount_path="/data", name=dep_name)]
            )

            volumes = client.V1Volume(
                name=dep_name,
                persistent_volume_claim=client.V1PersistentVolumeClaimVolumeSource(claim_name=pvc_name)
            )
            # spec
            template = client.V1PodTemplateSpec(
                metadata=client.V1ObjectMeta(labels={
                    'app': app_alias
                }),
                spec=client.V1PodSpec(
                    containers=[container],
                    image_pull_secrets=[image_pull_secret],
                    volumes=[volumes]
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

            service_port = client.V1ServicePort(port=3000, target_port=app_port)

            service_spec = client.V1ServiceSpec(
                type='ClusterIP',
                ports=[service_port],
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

            # subdomain for the app
            # sub_domain = f'{app_alias}.cranecloud.io'
            sub_domain = get_app_subdomain(app_alias)

            # create new ingress rule for the application
            new_ingress_backend = client.ExtensionsV1beta1IngressBackend(
                service_name=service_name,
                service_port=3000
                )

            new_ingress_rule = client.ExtensionsV1beta1IngressRule(
                host=sub_domain,
                http=client.ExtensionsV1beta1HTTPIngressRuleValue(
                    paths=[client.ExtensionsV1beta1HTTPIngressPath(
                        path="",
                        backend=new_ingress_backend
                        )]
                    )
                )

            ingress_name = f'{project.alias}-ingress'

            # Check if there is an ingress resource in the namespace, create if not

            ingress_list = kube_client.extension_api.list_namespaced_ingress(
                namespace=namespace).items

            if not ingress_list:

                ingress_meta = client.V1ObjectMeta(
                    name=ingress_name
                )

                ingress_spec = client.ExtensionsV1beta1IngressSpec(
                    # backend=ingress_backend,
                    rules=[new_ingress_rule]
                )

                ingress_body = client.ExtensionsV1beta1Ingress(
                    metadata=ingress_meta,
                    spec=ingress_spec
                )

                kube_client.extension_api.create_namespaced_ingress(
                    namespace=namespace,
                    body=ingress_body
                )

                # update registry
                resource_registry['ingress_entry'] = True
            else:
                # Update ingress with new entry
                ingress = ingress_list[0]

                ingress.spec.rules.append(new_ingress_rule)

                kube_client.extension_api.patch_namespaced_ingress(
                    name=ingress_name,
                    namespace=namespace,
                    body=ingress
                )

            service_url = f'https://{sub_domain}'

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
            'app_service': False,
            'ingress_entry': False
        }

        current_user_id = get_jwt_identity()
        current_user_roles = get_jwt_claims()['roles']

        app_schema = AppSchema()

        app_data = request.get_json()

        validated_app_data, errors = app_schema.load(
            app_data, partial=("project_id",))

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
        # env_vars = validated_app_data['env_vars']
        env_vars = validated_app_data.get('env_vars', None)
        private_repo = validated_app_data.get('private_image', False)
        docker_server = validated_app_data.get('docker_server', None)
        docker_username = validated_app_data.get('docker_username', None)
        docker_password = validated_app_data.get('docker_password', None)
        docker_email = validated_app_data.get('docker_email', None)
        replicas = validated_app_data.get('replicas', 1)
        app_port = validated_app_data.get('port', None)
        image_pull_secret = None

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

                image_pull_secret = client.V1LocalObjectReference(
                    name=app_alias)

            # create app deployment's pvc meta and spec
            pvc_name = f'{app_alias}-pvc'
            pvc_meta = client.V1ObjectMeta(name=pvc_name)

            access_modes = ['ReadWriteOnce']
            storage_class = 'openebs-standard'
            resources = client.V1ResourceRequirements(
                requests=dict(storage='1Gi'))

            pvc_spec = client.V1PersistentVolumeClaimSpec(
                access_modes=access_modes, resources=resources, storage_class_name=storage_class)

            # Create a PVC 
            pvc = client.V1PersistentVolumeClaim(
                api_version="v1",
                kind="PersistentVolumeClaim", 
                metadata=pvc_meta,
                spec=pvc_spec
            )

            # kube_client.kube.create_namespaced_persistent_volume_claim(
            #     namespace=namespace,
            #     body=pvc
            # )


            # create deployment
            dep_name = f'{app_alias}-deployment'

            # # EnvVar
            env = []
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
                # volume_mounts=[client.V1VolumeMount(mount_path="/data", name=dep_name)]
            )

            #pod volumes 
            volumes = client.V1Volume(
                name=dep_name
                # persistent_volume_claim=client.V1PersistentVolumeClaimVolumeSource(claim_name=pvc_name)
            )

            # spec
            template = client.V1PodTemplateSpec(
                metadata=client.V1ObjectMeta(labels={
                    'app': app_alias
                }),
                spec=client.V1PodSpec(
                    containers=[container],
                    image_pull_secrets=[image_pull_secret]
                    # volumes=[volumes]
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
                type='ClusterIP',
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

            # subdomain for the app
            # sub_domain = f'{app_alias}.cranecloud.io'
            sub_domain = get_app_subdomain(app_alias)

            # create new ingres rule for the application
            new_ingress_backend = client.ExtensionsV1beta1IngressBackend(
                service_name=service_name,
                service_port=3000
                )

            new_ingress_rule = client.ExtensionsV1beta1IngressRule(
                host=sub_domain,
                http=client.ExtensionsV1beta1HTTPIngressRuleValue(
                    paths=[client.ExtensionsV1beta1HTTPIngressPath(
                        path="",
                        backend=new_ingress_backend
                        )]
                    )
                )

            ingress_name = f'{project.alias}-ingress'

            # Check if there is an ingress resource in the namespace, create if not

            ingress_list = kube_client.extension_api.list_namespaced_ingress(
                namespace=namespace).items

            if not ingress_list:

                ingress_meta = client.V1ObjectMeta(
                    name=ingress_name
                )

                ingress_spec = client.ExtensionsV1beta1IngressSpec(
                    # backend=ingress_backend,
                    rules=[new_ingress_rule]
                )

                ingress_body = client.ExtensionsV1beta1Ingress(
                    metadata=ingress_meta,
                    spec=ingress_spec
                )

                kube_client.extension_api.create_namespaced_ingress(
                    namespace=namespace,
                    body=ingress_body
                )

                # update registry
                resource_registry['ingress_entry'] = True
            else:
                # Update ingress with new entry
                ingress = ingress_list[0]

                ingress.spec.rules.append(new_ingress_rule)

                kube_client.extension_api.patch_namespaced_ingress(
                    name=ingress_name,
                    namespace=namespace,
                    body=ingress
                )

            service_url = f'https://{sub_domain}'

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

            #delete pvc 
            pvc_name = f'{app.alias}-pvc'

            pvc = kube_client.kube.read_namespaced_persistent_volume_claim(
                name=pvc_name,
                namespace=namespace
            )

            if pvc:
                kube_client.kube.delete_namespaced_persistent_volume_claim(
                    name=pvc_name,
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
        try:
            for value in new_data["data"]["result"][0]["values"]:
                mem_case = {'timestamp': float(
                    value[0]), 'value': float(value[1])}
                final_data_list.append(mem_case)
        except:
            return dict(status='fail', message='No values found'), 404

        return dict(status='success', data=dict(values=final_data_list)), 200


class AppCpuUsageView(Resource):
    @jwt_required
    def post(self, project_id, app_id):

        current_user_id = get_jwt_identity()
        current_user_roles = get_jwt_claims()['roles']

        app_memory_schema = MetricsSchema()
        app_cpu_data = request.get_json()

        validated_query_data, errors = app_memory_schema.load(app_cpu_data)

        if errors:
            return dict(status='fail', message=errors), 400

        project = Project.get_by_id(project_id)

        if not project:
            return dict(
                status='fail',
                message=f'project {project_id} not found'
            ), 404

        if not is_owner_or_admin(project, current_user_id, current_user_roles):
            return dict(status='fail', message='unauthorised'), 403

        # Check app from db
        app = App.get_by_id(app_id)

        if not app:
            return dict(
                status='fail',
                message=f'app {app_id} not found'
            ), 404

        # Get current time
        current_time = datetime.datetime.now()
        yesterday = current_time + datetime.timedelta(days=-1)
        namespace = project.alias
        app_alias = app.alias

        prometheus = Prometheus()

        start = validated_query_data.get('start', yesterday.timestamp())
        end = validated_query_data.get('end', current_time.timestamp())
        step = validated_query_data.get('step', '1h')

        prom_data = prometheus.query_rang(
            start=start,
            end=end,
            step=step,
            metric='sum(rate(container_cpu_usage_seconds_total{container!="POD", image!="", namespace="' +
            namespace+'", pod=~"'+app_alias+'.*"}[5m]))'
        )
        #  change array values to json"values"
        new_data = json.loads(prom_data)
        cpu_data_list = []
        try:
            for value in new_data["data"]["result"][0]["values"]:
                case = {'timestamp': float(value[0]), 'value': float(value[1])}
                cpu_data_list.append(case)
        except:
            return dict(status='fail', message='No values found'), 404

        return dict(status='success', data=dict(values=cpu_data_list)), 200


class AppNetworkUsageView(Resource):
    @jwt_required
    def post(self, project_id, app_id):

        current_user_id = get_jwt_identity()
        current_user_roles = get_jwt_claims()['roles']

        app_network_schema = MetricsSchema()
        app_network_data = request.get_json()

        validated_query_data, errors = app_network_schema.load(
            app_network_data)

        if errors:
            return dict(status='fail', message=errors), 400

        project = Project.get_by_id(project_id)

        if not project:
            return dict(
                status='fail',
                message=f'project {project_id} not found'
            ), 404

        if not is_owner_or_admin(project, current_user_id, current_user_roles):
            return dict(status='fail', message='unauthorised'), 403

        # Check app from db
        app = App.get_by_id(app_id)

        if not app:
            return dict(
                status='fail',
                message=f'app {app_id} not found'
            ), 404

        # Get current time
        current_time = datetime.datetime.now()
        yesterday = current_time + datetime.timedelta(days=-1)
        namespace = project.alias
        app_alias = app.alias

        prometheus = Prometheus()

        start = validated_query_data.get('start', yesterday.timestamp())
        end = validated_query_data.get('end', current_time.timestamp())
        step = validated_query_data.get('step', '1h')

        prom_data = prometheus.query_rang(
            start=start,
            end=end,
            step=step,
            metric='sum(rate(container_network_receive_bytes_total{namespace="' +
            namespace+'", pod=~"'+app_alias+'.*"}[5m]))'
        )
        #  change array values to json "values"
        new_data = json.loads(prom_data)
        network_data_list = []
        try:
            for value in new_data["data"]["result"][0]["values"]:
                case = {'timestamp': float(value[0]), 'value': float(value[1])}
                network_data_list.append(case)
        except:
            return dict(status='fail', message='No values found'), 404

        return dict(status='success', data=dict(values=network_data_list)), 200


class AppLogsView(Resource):
    @jwt_required
    def post(self, project_id, app_id):

        current_user_id = get_jwt_identity()
        current_user_roles = get_jwt_claims()['roles']

        logs_schema = PodsLogsSchema()
        logs_data = request.get_json()

        validated_query_data, errors = logs_schema.load(logs_data)

        if errors:
            return dict(status='fail', message=errors), 400

        project = Project.get_by_id(project_id)

        if not project:
            return dict(
                status='fail',
                message=f'project {project_id} not found'
            ), 404

        if not is_owner_or_admin(project, current_user_id, current_user_roles):
            return dict(status='fail', message='unauthorised'), 403

        # Check app from db
        app = App.get_by_id(app_id)

        if not app:
            return dict(
                status='fail',
                message=f'app {app_id} not found'
            ), 404

        cluster = project.cluster
        if not cluster:
            return dict(status='fail', message="Invalid Cluster"), 500

        kube_host = cluster.host
        kube_token = cluster.token
        kube_client = create_kube_clients(kube_host, kube_token)

        namespace = project.alias
        deployment = app.alias

        tail_lines = validated_query_data.get('tail_lines', 100)
        since_seconds = validated_query_data.get('since_seconds', 86400)
        timestamps = validated_query_data.get('timestamps', False)

        ''' Get Replicas sets'''
        replicas = kube_client.appsv1_api.list_namespaced_replica_set(
            namespace).to_dict()
        replicasList = []
        for replica in replicas['items']:
            name = replica['metadata']['name']
            if name.startswith(deployment):
                replicasList.append(name)

        ''' get pods list'''
        pods = kube_client.kube.list_namespaced_pod(namespace)
        podsList = []
        failed_pods = []
        for item in pods.items:
            item = kube_client.api_client.sanitize_for_serialization(item)
            pod_name = item['metadata']['name']

            try:
                status = item['status']['conditions'][1]['status']
            except:
                continue

            for replica in replicasList:
                if pod_name.startswith(replica):
                    if status == 'True':
                        podsList.append(pod_name)
                    else:
                        failed_pods.append(pod_name)
                    continue

            if pod_name.startswith(deployment):
                if status == 'True':
                    podsList.append(pod_name)
                else:
                    state = item['status']['containerStatuses'][0]['state']
                    failed_pods.append(state)

        ''' Get pods logs '''
        pods_logs = []

        for pod in podsList:
            podLogs = kube_client.kube.read_namespaced_pod_log(
                pod, namespace, pretty=True, tail_lines=tail_lines or 100,
                timestamps=timestamps or False,
                since_seconds=since_seconds or 86400
            )

            if podLogs == '':
                podLogs = kube_client.kube.read_namespaced_pod_log(
                    pod, namespace, pretty=True, tail_lines=tail_lines or 100,
                    timestamps=timestamps or False
                )
            pods_logs.append(podLogs)

        # Get failed pods infor
        for state in failed_pods:
            waiting = state.get('waiting')
            if waiting:
                try:
                    stop = state['waiting']['message'].index('container')
                    message = state['waiting']['message'][:stop]
                except:
                    message = state['waiting']['message']

                reason = state['waiting']['reason']
                pod_infor = f'type\tstatus\treason\t\t\tmessage\n----\t------\t------\t\t\t------\nwaiting\tfailed\t{reason}\t{message}'
                pods_logs.append(pod_infor)

        if not pods_logs or not pods_logs[0]:
            return dict(status='fail', data=dict(message='No logs found')), 404

        return dict(status='success', data=dict(pods_logs=pods_logs)), 200


class AppStorageUsageView(Resource):
    @jwt_required
    def post(self, project_id, app_id):

        current_user_id = get_jwt_identity()
        current_user_roles = get_jwt_claims()['roles']

        project = Project.get_by_id(project_id)

        if not project:
            return dict(
                status='fail',
                message=f'project {project_id} not found'
            ), 404

        if not is_owner_or_admin(project, current_user_id, current_user_roles):
            return dict(status='fail', message='unauthorised'), 403

        # Check app from db
        app = App.get_by_id(app_id)

        if not app:
            return dict(
                status='fail',
                message=f'app {app_id} not found'
            ), 404

        namespace = project.alias
        app_alias = app.alias

        prometheus = Prometheus()

        try:
            prom_data = prometheus.query( metric='sum(kube_persistentvolumeclaim_resource_requests_storage_bytes{namespace="' +
                namespace+'", persistentvolumeclaim=~"'+app_alias+'.*"})'
            )
            #  change array values to json 
            new_data = json.loads(prom_data)
            values = new_data["data"]

            percentage_data = prometheus.query( metric='100*(kubelet_volume_stats_used_bytes{namespace="' +
                namespace+'", persistentvolumeclaim=~"'+app_alias+'.*"}/kubelet_volume_stats_capacity_bytes{namespace="' +
                namespace+'", persistentvolumeclaim=~"'+app_alias+'.*"})'
            )

            data = json.loads(percentage_data)
            volume_perc_value = data["data"]
        except:
            return dict(status='fail', message='No values found'), 404

        return dict(status='success', data=dict(storage_capacity=values,storage_percentage_usage=volume_perc_value)), 200
