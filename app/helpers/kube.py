import os
from types import SimpleNamespace
from app.helpers.db_flavor import get_db_flavour
from app.models.project_database import ProjectDatabase
from kubernetes import client
from kubernetes.client.rest import ApiException
import base64
import json
from app.helpers.activity_logger import log_activity
from app.helpers.clean_up import resource_clean_up
from app.helpers.url import get_app_subdomain


def create_kube_clients(kube_host=os.getenv('KUBE_HOST'), kube_token=os.getenv('KUBE_TOKEN')):
    # configure client
    config = client.Configuration()
    config.host = kube_host
    config.api_key['authorization'] = kube_token
    config.api_key_prefix['authorization'] = 'Bearer'
    config.verify_ssl = False
    # config.assert_hostname = False

    # create API instance
    api_client = client.ApiClient()
    kube = client.CoreV1Api(client.ApiClient(config))
    # extension_api = client.ExtensionsV1beta1Api(client.ApiClient(config))
    appsv1_api = client.AppsV1Api(client.ApiClient(config))
    batchv1_api = client.BatchV1Api(client.ApiClient(config))
    storageV1Api = client.StorageV1Api(client.ApiClient(config))
    networking_api = client.NetworkingV1Api(client.ApiClient(config))

    # return kube, extension_api, appsv1_api, api_client, batchv1_api, storageV1Api
    return SimpleNamespace(
        kube=kube,
        # extension_api=extension_api,
        networking_api=networking_api,
        appsv1_api=appsv1_api,
        api_client=api_client,
        batchv1_api=batchv1_api,
        storageV1Api=storageV1Api
    )


def delete_cluster_app(kube_client, namespace, app):
    # delete deployment and service for the app

    deployment_name = f'{app.alias}-deployment'
    service_name = f'{app.alias}-service'
    try:

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

        secret = kube_client.kube.read_namespaced_secret(
            name=app.alias,
            namespace=namespace
        )
        kube_client.kube.delete_namespaced_secret(
            name=app.alias,
            namespace=namespace
        )
    except Exception as e:
        if e.status != 404:
            return dict(status='fail', message=str(e)), 500

    # delete pvc
    # pvc_name = f'{app.alias}-pvc'

    # pvc = kube_client.kube.read_namespaced_persistent_volume_claim(
    #     name=pvc_name,
    #     namespace=namespace
    # )

    # if pvc:
    #     kube_client.kube.delete_namespaced_persistent_volume_claim(
    #         name=pvc_name,
    #         namespace=namespace
    #     )


def create_user_app(
    new_app,
    app_alias,
    app_image,
    project,
    command_string=None,
    env_vars=None,
    private_repo=False,
    docker_server=None,
    docker_username=None,
    docker_password=None,
    docker_email=None,
    replicas=1,
    app_port=80,
):
    """
    Function to create user application
    """

    resource_registry = {
        'db_deployment': False,
        'db_service': False,
        'image_pull_secret': False,
        'app_deployment': False,
        'app_service': False,
        'ingress_entry': False
    }
    image_pull_secret = None
    command = command_string.split() if command_string else None

    cluster = project.cluster
    namespace = project.alias

    if not cluster:
        return SimpleNamespace(
            message="Invalid Cluster",
            status_code=500
        )

    kube_host = cluster.host
    kube_token = cluster.token

    kube_client = create_kube_clients(kube_host, kube_token)

    try:
        # check if namespace exisits
        try:
            kube_client.kube.read_namespace(namespace)
        except ApiException as e:
            if e.status == 404:
                # create namespace in cluster
                kube_client.kube.create_namespace(
                    client.V1Namespace(
                        metadata=client.V1ObjectMeta(name=namespace)
                    ))

        try:
            # Check if app is in the cluster
            kube_client.appsv1_api.read_namespaced_deployment_status(
                app_alias + "-deployment", project.alias)
            return SimpleNamespace(
                message='App already exists on the server',
                status_code=409
            )
        except:
            pass

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

        service_port = client.V1ServicePort(
            port=3000, target_port=app_port)

        service_spec = client.V1ServiceSpec(
            type='ClusterIP',
            ports=[service_port],
            selector={'app': app_alias}
        )

        service = client.V1Service(
            metadata=service_meta,
            spec=service_spec)

        try:
            # Check if service exists in the cluster
            kube_client.kube.read_namespaced_service(
                service_name, project.alias)
            # Delete service
            kube_client.kube.delete_namespaced_service(
                service_name, project.alias)
        except:
            pass

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
        new_ingress_backend = client.V1IngressBackend(
            service=client.V1IngressServiceBackend(
                name=service_name,
                port=client.V1ServiceBackendPort(
                    number=3000
                )
            )
        )

        new_ingress_rule = client.V1IngressRule(
            host=sub_domain,
            http=client.V1HTTPIngressRuleValue(
                paths=[client.V1HTTPIngressPath(
                    path="",
                    path_type="ImplementationSpecific",
                    backend=new_ingress_backend
                )]
            )
        )

        ingress_name = f'{project.alias}-ingress'

        # Check if there is an ingress resource in the namespace, create if not
        # TODO: Remove the try and handle the error

        try:
            ingress_list = kube_client.networking_api.list_namespaced_ingress(
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

                kube_client.networking_api.create_namespaced_ingress(
                    namespace=namespace,
                    body=ingress_body
                )

                # update registry
                resource_registry['ingress_entry'] = True
            else:
                # Update ingress with new entry
                ingress = ingress_list[0]

                ingress.spec.rules.append(new_ingress_rule)

                kube_client.networking_api.patch_namespaced_ingress(
                    name=ingress_name,
                    namespace=namespace,
                    body=ingress
                )
        except client.rest.ApiException as e:
            print(e)
        except Exception:
            pass

        service_url = f'https://{sub_domain}'

        new_app.url = service_url

        saved = new_app.save()

        if not saved:
            log_activity('App', status='Failed',
                         operation='Create',
                         description='Internal Server Error',
                         a_project_id=project.id,
                         a_cluster_id=project.cluster_id)
            return SimpleNamespace(
                message='Internal Server Error',
                status_code=500
            )

        # log_activity('App', status='Success',
        #              operation='Create',
        #              description='Created app Successfully',
        #              a_project_id=project.id,
        #              a_cluster_id=project.cluster_id,
        #              a_app_id=new_app.id)
        return new_app

    except client.rest.ApiException as e:
        resource_clean_up(
            resource_registry,
            app_alias,
            namespace,
            kube_client
        )

        log_activity('App', status='Failed',
                     operation='Create',
                     description=json.loads(e.body),
                     a_project_id=project.id,
                     a_cluster_id=project.cluster_id,
                     )
        return SimpleNamespace(
            message=json.loads(e.body),
            status_code=500
        )

    except Exception as e:
        resource_clean_up(
            resource_registry,
            app_alias,
            namespace,
            kube_client
        )
        log_activity('App', status='Failed',
                     operation='Create',
                     description=str(e),
                     a_project_id=project.id,
                     a_cluster_id=project.cluster_id,
                     )
        return SimpleNamespace(
            message=str(e),
            status_code=500
        )


def disable_user_app(app, is_admin=False):
    try:
        kube_host = app.project.cluster.host
        kube_token = app.project.cluster.token

        kube_client = create_kube_clients(kube_host, kube_token)

        # scale apps down to 0
        try:
            app_name = f'{app.alias}-deployment'
            deployment = kube_client.appsv1_api.read_namespaced_deployment(
                name=app_name,
                namespace=app.project.alias
            )
            deployment.spec.replicas = 0

            # Apply the updated Deployment spec
            kube_client.appsv1_api.replace_namespaced_deployment(
                name=app_name,
                namespace=app.project.alias,
                body=deployment
            )
        except:
            pass
        # save app
        app.disabled = True
        if is_admin:
            app.admin_disabled = True
        app.save()

        log_activity('App', status='Success',
                     operation='Disable',
                     description='Disabled app Successfully',
                     a_project_id=app.project.id,
                     a_cluster_id=app.project.cluster_id)
        return True

    except client.rest.ApiException as e:
        log_activity('App', status='Failed',
                     operation='Disable',
                     description='Error disabling application',
                     a_project_id=app.project.id,
                     a_cluster_id=app.project.cluster_id)
        return SimpleNamespace(
            message=json.loads(e.body),
            status_code=500
        )

    except Exception as err:
        return SimpleNamespace(
            message=str(err),
            status_code=500
        )


def enable_user_app(app):
    try:
        kube_host = app.project.cluster.host
        kube_token = app.project.cluster.token

        kube_client = create_kube_clients(kube_host, kube_token)

        try:
            app_name = f'{app.alias}-deployment'
            deployment = kube_client.appsv1_api.read_namespaced_deployment(
                name=app_name,
                namespace=app.project.alias
            )
            deployment.spec.replicas = app.replicas

            # Apply the updated Deployment spec
            kube_client.appsv1_api.replace_namespaced_deployment(
                name=app_name,
                namespace=app.project.alias,
                body=deployment
            )
        except:
            pass
        # save app
        app.disabled = False
        app.admin_disabled = False
        app.save()

        log_activity('App', status='Success',
                     operation='Enable',
                     description='Enabled app Successfully',
                     a_project_id=app.project.id,
                     a_cluster_id=app.project.cluster_id)
        return True

    except client.rest.ApiException as e:
        log_activity('App', status='Failed',
                     operation='Enable',
                     description='Error enabling application',
                     a_project_id=app.project.id,
                     a_cluster_id=app.project.cluster_id)
        return SimpleNamespace(
            message=json.loads(e.body),
            status_code=500
        )

    except Exception as err:
        return SimpleNamespace(
            message=str(err),
            status_code=500
        )


def disable_project(project, is_admin=False):
    # get postgres project databases
    db_flavour = 'postgres'
    psql_project_databases = ProjectDatabase.find_all(
        project_id=project.id, database_flavour_name=db_flavour)

    if psql_project_databases:

        # get connection
        db_flavour = get_db_flavour(db_flavour)
        database_service = db_flavour['class']
        database_connection = database_service.check_db_connection()

        if not database_connection:
            log_activity('Database', status='Failed',
                         operation='Disable',
                         description='Failed to connect to the database service, Internal Server Error',
                         a_project_id=project.id,
                         a_cluster_id=project.cluster_id
                         )
            return SimpleNamespace(
                message="Failed to connect to the database service",
                status_code=500
            )

        # Disable the postgres databases
        for database in psql_project_databases:

            # check if disabled
            if not database.disabled:
                disable_database = database_service.disable_user_log_in(
                    database.user)

                if not disable_database:
                    log_activity('Database', status='Failed',
                                 operation='Disable',
                                 description='Unable to disable postgres database, Internal Server Error',
                                 a_project_id=project.id,
                                 a_cluster_id=project.cluster_id
                                 )

                    return SimpleNamespace(
                        message="Unable to disable database",
                        status_code=500
                    )
                database.disabled = True
                if is_admin:
                    database.admin_disabled = True
                database.save()

    # get mysql project databases
    db_flavour = 'mysql'
    mysql_project_databases = ProjectDatabase.find_all(
        project_id=project.id, database_flavour_name=db_flavour)

    if mysql_project_databases:

        # get connection
        db_flavour = get_db_flavour(db_flavour)
        database_service = db_flavour['class']
        database_connection = database_service.check_db_connection()

        if not database_connection:
            log_activity('Database', status='Failed',
                         operation='Disable',
                         description='Failed to connect to the database service, Internal Server Error',
                         a_project_id=project.id,
                         a_cluster_id=project.cluster_id
                         )

            return SimpleNamespace(
                message="Failed to connect to the database service",
                status_code=500
            )

        # Disable mysql databases
        for database in mysql_project_databases:
            # check if disabled
            if not database.disabled:

                disable_database = database_service.disable_user_log_in(
                    database.user, database.password)

                if not disable_database:
                    log_activity('Database', status='Failed',
                                 operation='Disable',
                                 description='Unable to disable mysql database, Internal Server Error',
                                 a_project_id=project.id,
                                 a_cluster_id=project.cluster_id)

                    return SimpleNamespace(
                        message="Unable to disable database",
                        status_code=500
                    )
                database.disabled = True
                if is_admin:
                    database.admin_disabled = True
                database.save()

    # Disable apps
    try:
        kube_host = project.cluster.host
        kube_token = project.cluster.token

        kube_client = create_kube_clients(kube_host, kube_token)

        # scale apps down to 0
        for app in project.apps:
            disable_user_app(app, is_admin)

        # Add resource quota
        quota = client.V1ResourceQuota(
            api_version="v1",
            kind="ResourceQuota",
            metadata=client.V1ObjectMeta(
                name="disable-quota", namespace=project.alias),
            spec=client.V1ResourceQuotaSpec(
                hard={
                    "requests.cpu": "0",
                    "requests.memory": "0",
                    "limits.cpu": "0",
                    "limits.memory": "0"
                }
            )
        )

        kube_client.kube.create_namespaced_resource_quota(
            project.alias, quota)

        # save project
        project.disabled = True
        if is_admin:
            project.admin_disabled = True
        project.save()

        log_activity('Project', status='Success',
                     operation='Disable',
                     description='Disabled project Successfully',
                     a_project_id=project.id,
                     a_cluster_id=project.cluster_id)
        return True
    except client.rest.ApiException as e:
        if e.status == 404:
            # save project
            project.disabled = True
            if is_admin:
                project.admin_disabled = True
            project.save()
            log_activity('Project', status='Success',
                         operation='Disable',
                         description='Disabled project but doesnt exist in the cluster',
                         a_project_id=project.id,
                         a_cluster_id=project.cluster_id)
            return True
        log_activity('Project', status='Failed',
                     operation='Disable',
                     description='Error disabling application',
                     a_project_id=project.id,
                     a_cluster_id=project.cluster_id)
        return SimpleNamespace(
            message=str(e.body),
            status_code=500
        )

    except Exception as err:
        log_activity('Project', status='Failed',
                     operation='Disable',
                     description=err.body,
                     a_project_id=project.id,
                     a_cluster_id=project.cluster_id)
        return SimpleNamespace(
            message=str(err),
            status_code=500
        )


def enable_project(project):
    # get postgres project databases
    db_flavour = 'postgres'
    psql_project_databases = ProjectDatabase.find_all(
        project_id=project.id, database_flavour_name=db_flavour)

    if psql_project_databases:

        # get connection
        db_flavour = get_db_flavour(db_flavour)
        database_service = db_flavour['class']
        database_connection = database_service.check_db_connection()

        if not database_connection:
            log_activity('Database', status='Failed',
                         operation='Enable',
                         description='Failed to connect to the database service, Internal Server Error',
                         a_project_id=project.id,
                         a_cluster_id=project.cluster_id
                         )

            return SimpleNamespace(
                message=f"Failed to connect to the database service",
                status_code=500
            )

        # Enable the postgres databases
        for database in psql_project_databases:

            # check if disabled
            if database.disabled:

                disable_database = database_service.enable_user_log_in(
                    database.user)

                if not disable_database:
                    log_activity('Database', status='Failed',
                                 operation='Enable',
                                 description='Unable to enable postgres database, Internal Server Error',
                                 a_project_id=project.id,
                                 a_cluster_id=project.cluster_id)

                    return SimpleNamespace(
                        message=f"Unable to enable database",
                        status_code=500
                    )

                database.disabled = False
                database.admin_disabled = False
                database.save()

    # get mysql project databases
    db_flavour = 'mysql'
    mysql_project_databases = ProjectDatabase.find_all(
        project_id=project.id, database_flavour_name=db_flavour)

    if mysql_project_databases:

        # get connection
        db_flavour = get_db_flavour(db_flavour)
        database_service = db_flavour['class']
        database_connection = database_service.check_db_connection()

        if not database_connection:
            log_activity('Database', status='Failed',
                         operation='Enable',
                         description='Failed to connect to the database service, Internal Server Error',
                         a_project_id=project.id,
                         a_cluster_id=project.cluster_id
                         )

            return SimpleNamespace(
                message=f"Failed to connect to the database service",
                status_code=500
            )

        # Enable mysql databases
        for database in mysql_project_databases:

            # check if disabled
            if database.disabled:

                disable_database = database_service.enable_user_log_in(
                    database.user, database.password)

                if not disable_database:
                    log_activity('Database', status='Failed',
                                 operation='Enable',
                                 description='Unable to disable mysql database, Internal Server Error',
                                 a_project_id=project.id,
                                 a_cluster_id=project.cluster_id
                                 )

                    return SimpleNamespace(
                        message=f"Unable to enable database",
                        status_code=500
                    )

                database.disabled = False
                database.admin_disabled = False
                database.save()

    # Enable apps
    try:
        kube_host = project.cluster.host
        kube_token = project.cluster.token

        kube_client = create_kube_clients(kube_host, kube_token)
        try:
            for app in project.apps:
                enable_user_app(app)

            # Delete the ResourceQuota
            kube_client.kube.delete_namespaced_resource_quota(
                name='disable-quota', namespace=project.alias
            )
        except client.rest.ApiException as e:
            if e.status != 404:
                log_activity('Project', status='Failed',
                             operation='Enable',
                             description=f'Error enabling the project. {e.body}',
                             a_project_id=project.id,
                             a_cluster_id=project.cluster_id)
                return SimpleNamespace(
                    message=str(e.body),
                    status_code=e.status
                )

        # save project
        project.disabled = False
        project.admin_disabled = False
        project.save()

        log_activity('Project', status='Success',
                     operation='Enable',
                     description='Enabled project Successfully',
                     a_project_id=project.id,
                     a_cluster_id=project.cluster_id)
        return True

    except Exception as err:
        log_activity('Project', status='Failed',
                     operation='Enable',
                     description=err.body,
                     a_project_id=project.id,
                     a_cluster_id=project.cluster_id)
        return SimpleNamespace(
            message=str(err),
            status_code=500
        )
