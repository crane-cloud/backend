import base64
import datetime
import json
import os
from urllib.parse import urlsplit
from app.helpers.activity_logger import log_activity
from app.schemas.app import AppDeploySchema
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt_claims
from flask_restful import Resource, request
from kubernetes import client
from prometheus_http_client import Prometheus
from types import SimpleNamespace
from app.models.app import App
from app.models.project import Project
from app.helpers.kube import (create_kube_clients, delete_cluster_app,
                              disable_user_app, enable_user_app, sort_apps_for_deployment, update_app_env_vars)
from app.schemas import AppSchema, MetricsSchema, PodsLogsSchema, AppGraphSchema
from app.helpers.admin import is_admin, is_authorised_project_user, is_owner_or_admin
from app.helpers.decorators import admin_required
from app.helpers.decorators import admin_required
from app.helpers.kube import create_kube_clients, delete_cluster_app, deploy_user_app, check_kube_error_code
from app.helpers.url import get_app_subdomain
from app.models.app import App
from app.models.app_state import AppState
from app.models.user import User
from app.models.clusters import Cluster
from app.models.project import Project
from app.schemas import AppSchema, MetricsSchema, PodsLogsSchema, AppGraphSchema, AppStateSchema
from app.helpers.crane_app_logger import logger
from app.helpers.pagination import paginate
from app.helpers.app_status_updater import update_or_create_app_state
from app.models import db


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

        app_name = validated_app_data['name']
        project_id = validated_app_data['project_id']

        project = Project.get_by_id(project_id)

        if not project:
            return dict(status='fail', message=f'Project {project_id} not found'), 404

        cluster = project.cluster

        if not cluster:
            return dict(status='fail', message="Invalid Cluster"), 500

        # check if app already exists
        app = App.find_first(**{'name': app_name})

        if app:
            log_activity('App', status='Failed',
                         operation='Create',
                         description=f'App {app_name} already exists',
                         a_project_id=project.id,
                         a_cluster_id=project.cluster_id)
            return dict(status='fail', message=f'App {app_name} already exists'), 409

        user = User.get_by_id(get_jwt_identity())

        kube_host = cluster.host
        kube_token = cluster.token

        kube_client = create_kube_clients(kube_host, kube_token)
        service_host = urlsplit(kube_host).hostname

        new_app = deploy_user_app(
            kube_client=kube_client, project=project, user=user, app_data=validated_app_data)

        if type(new_app) == SimpleNamespace:
            status_code = new_app.status_code if new_app.status_code else 500
            return dict(status='fail', message=new_app.message), status_code

        new_app_data, _ = app_schema.dump(new_app)
        log_activity('App', status='Success',
                     operation='Create',
                     description='Deployed app Successfully',
                     a_project_id=project.id,
                     a_cluster_id=project.cluster_id,
                     a_app_id=new_app.id)

        return dict(status='success', data=dict(app=new_app_data)), 201

    @admin_required
    def get(self):
        """
        Get overall app information
        """

        graph_filter_data = {
            'start': request.args.get('start', '2018-01-01'),
            'end': request.args.get('end', datetime.datetime.now().strftime('%Y-%m-%d')),
            'set_by': request.args.get('set_by', 'month'),
            'disabled': request.args.get('disabled'),
        }
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        series = request.args.get('series', False)
        disabled = request.args.get('disabled', False) == "true"
        active = request.args.get('active', False) == "true"

        if isinstance(series, str):
            series = series.lower() == 'true'

        filter_schema = AppGraphSchema()
        apps_schema = AppSchema(many=True)

        # since it is a one to one
        metadata = {
            'disabled': App.query.filter_by(disabled=True).count(),
            'total_apps': App.query.count(),
            'failing_apps': AppState.query.filter_by(status="failed").count(),
            'running_apps': AppState.query.filter_by(status="running").count(),
        }

        if not series:
            paginated_apps = App.query.paginate(
                page=page, per_page=per_page, error_out=False)
            if disabled:
                paginated_apps = App.query.filter_by(disabled=True).paginate(
                    page=page, per_page=per_page, error_out=False)
            if active:
                paginated_apps = App.query.filter_by(disabled=False).paginate(
                    page=page, per_page=per_page, error_out=False)

            pagination = {
                'total': paginated_apps.total,
                'pages': paginated_apps.pages,
                'page': paginated_apps.page,
                'per_page': paginated_apps.per_page,
                'next': paginated_apps.next_num,
                'prev': paginated_apps.prev_num
            }
            apps = paginated_apps.items
            apps_data, errors = apps_schema.dumps(apps)
            # pagination = apps.pagination

            if errors:
                return dict(status='fail', message=errors), 400

            return dict(
                status='success',
                data=dict(
                    metadata=metadata,
                    pagination=pagination,
                    apps=json.loads(apps_data))
            ), 200

        validated_query_data, errors = filter_schema.load(graph_filter_data)
        if errors:
            return dict(status='fail', message=errors), 400

        start = validated_query_data.get('start')
        end = validated_query_data.get('end')
        set_by = validated_query_data.get('set_by')

        app_info = App.graph_data(start=start, end=end, set_by=set_by)

        return dict(
            status='success',
            data=dict(
                metadata=metadata,
                graph_data=app_info)
        ), 200


class ProjectAppsView(Resource):

    @jwt_required
    def post(self, project_id):
        """
        """

        current_user_id = get_jwt_identity()
        current_user_roles = get_jwt_claims()['roles']

        app_schema = AppDeploySchema()

        app_data = request.get_json()

        validated_app_data, errors = app_schema.load(
            app_data, partial=("project_id",))

        if errors:
            return dict(status='fail', message=errors), 400

        project = Project.get_by_id(project_id)

        if not project:
            return dict(status='fail', message=f'project {project_id} not found'), 404

        if not is_owner_or_admin(project, current_user_id, current_user_roles):
            if not is_authorised_project_user(project, current_user_id, 'member'):
                return dict(status='fail', message='Unauthorised'), 403

        user = User.get_by_id(current_user_id)

        cluster = project.cluster

        if not cluster:
            return dict(status='fail', message="Invalid Cluster"), 500

        kube_host = cluster.host
        kube_token = cluster.token

        kube_client = create_kube_clients(kube_host, kube_token)
        multi_app = validated_app_data.get('apps', [])
        if multi_app:
            deployed_apps = sort_apps_for_deployment(
                apps_data=multi_app, kube_client=kube_client,
                project=project, user=user, app_schema=app_schema)
            return dict(status='success', data=dict(
                failed_apps=deployed_apps.failed_apps_data,
                apps=deployed_apps.apps_data)), 201
        else:
            app_name = validated_app_data.get('name', None)
            app_image = validated_app_data.get('image', None)
            if not app_name or not app_image:
                return dict(status='fail', data=dict(message="Missing data for required field, either name or image"))

            existing_app = App.find_first(
                name=app_name,
                project_id=project_id)

            if existing_app:
                log_activity('App', status='Failed',
                             operation='Create',
                             description=f'App {app_name} already exists',
                             a_project_id=project.id,
                             a_cluster_id=project.cluster_id)
                return dict(
                    status='fail',
                    message=f'App with name {app_name} already exists'
                ), 409

            new_app = deploy_user_app(
                kube_client=kube_client, project=project, user=user, app_data=validated_app_data)

            if type(new_app) == SimpleNamespace:
                status_code = new_app.status_code if new_app.status_code else 500
                return dict(status='fail', message=new_app.message), status_code

            new_app_data, _ = app_schema.dump(new_app)
            log_activity('App', status='Success',
                         operation='Create',
                         description='Deployed app Successfully',
                         a_project_id=project.id,
                         a_cluster_id=project.cluster_id,
                         a_app_id=new_app.id)

            return dict(status='success', data=dict(app=new_app_data)), 201

    @jwt_required
    def get(self, project_id):
        """
        """
        try:
            current_user_id = get_jwt_identity()
            current_user_roles = get_jwt_claims()['roles']
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 10, type=int)
            keywords = request.args.get('keywords', '')
            app_schema = AppSchema(many=True)

            project = Project.get_by_id(project_id)

            if not project:
                return dict(status='fail', message=f'project {project_id} not found'), 404

            if not is_owner_or_admin(project, current_user_id, current_user_roles):
                if not is_authorised_project_user(project, current_user_id, 'member'):
                    return dict(status='fail', message='Unauthorised'), 403

            cluster = Cluster.get_by_id(project.cluster_id)

            if not cluster:
                return dict(status='fail', message=f'cluster with id {project.cluster_id} does not exist'), 404

            kube_host = cluster.host
            kube_token = cluster.token
            kube_client = create_kube_clients(kube_host, kube_token)

            if (keywords == ''):
                paginated = App.find_all(
                    project_id=project_id, paginate=True, page=page, per_page=per_page)
                pagination = paginated.pagination
                apps = paginated.items
                apps_data, errors = app_schema.dumps(apps)

            else:
                paginated = App.query.filter(App.name.ilike('%'+keywords+'%'), App.project_id == project_id).order_by(
                    App.date_created.desc()).paginate(page=page, per_page=per_page, error_out=False)
                pagination = {
                    'total': paginated.total,
                    'pages': paginated.pages,
                    'page': paginated.page,
                    'per_page': paginated.per_page,
                    'next': paginated.next_num,
                    'prev': paginated.prev_num
                }
                apps = paginated.items
                apps_data, errors = app_schema.dumps(apps)

            # if errors:
            #     return dict(status='fail', message=errors), 500

            apps_data_list = json.loads(apps_data)
            for app in apps_data_list:
                try:
                    # Dont check status of disabled apps
                    if app['disabled']:
                        app['app_running_status'] = "disabled"
                        continue
                    app_status_object = \
                        kube_client.appsv1_api.read_namespaced_deployment_status(
                            app['alias'] + "-deployment", project.alias)
                    app_deployment_status_conditions = app_status_object.status.conditions

                    app_deployment_status = None
                    if app_deployment_status_conditions:
                        for deplyoment_status_condition in app_deployment_status_conditions:
                            if deplyoment_status_condition.type == "Available":
                                app_deployment_status = deplyoment_status_condition.status

                except client.rest.ApiException:
                    app_deployment_status = None

                try:
                    app_db_status_object = \
                        kube_client.appsv1_api.read_namespaced_deployment_status(
                            app['alias'] + "-postgres-db", project.alias)

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
            if errors:
                return dict(status='error', error=errors, data=dict(apps=apps_data_list)), 409
            return dict(status='success',
                        data=dict(pagination=pagination, apps=apps_data_list)), 200

        except client.rest.ApiException as exc:
            return dict(status='fail', message=exc.reason), check_kube_error_code(exc.status)

        except Exception as exc:
            return dict(status='fail', message=str(exc)), 500


class AppDetailView(Resource):

    @jwt_required
    def get(self, app_id):
        """
        get single application details
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
                if not is_authorised_project_user(project, current_user_id, 'member'):
                    return dict(status='fail', message='Unauthorised'), 403

            app_data, errors = app_schema.dumps(app)

            # if errors:
            #     return dict(status='fail', message=errors), 500

            app_list = json.loads(app_data)

            cluster = Cluster.get_by_id(project.cluster_id)
            # st = AppState.query.filter_by(app=app_id).first()

            if not cluster:
                return dict(
                    status='fail',
                    message=f'cluster with id {project.cluster_id} does not exist'), 404

            kube_host = cluster.host
            kube_token = cluster.token
            kube_client = create_kube_clients(kube_host, kube_token)

            app_status_object = \
                kube_client.appsv1_api.read_namespaced_deployment_status(
                    app_list['alias'] + "-deployment", project.alias)

            ''' get replica list'''
            replicas = kube_client.appsv1_api.list_namespaced_replica_set(
                project.alias).to_dict()
            replicasList = []
            for replica in replicas['items']:
                name = replica['metadata']['name']
                if name.startswith(app_list['alias']):
                    replicasList.append(name)

            ''' get pods list'''
            pods = kube_client.kube.list_namespaced_pod(project.alias)
            podsList = []
            for item in pods.items:
                item = kube_client.api_client.sanitize_for_serialization(item)
                pod_name = item['metadata']['name']
                # to avoid repetition
                added = False

                for replica in replicasList:
                    if pod_name.startswith(replica):
                        podsList.append(item)
                        added = True
                        continue

                if pod_name.startswith(app_list['alias']) and not added:
                    podsList.append(item)
                    continue

            app_status_messages = []
            for index, pod_log in enumerate(podsList):
                pod_name = pod_log["metadata"]["name"]
                # pod_namespace = pod_log["metadata"]["namespace"]
                pod_status = pod_log["status"]["phase"]

                if pod_status == "Running":
                    app_status_messages.append({
                        "status": "running",
                        "message": f"Pod:{index} is running. ",
                        "replicaNumber": index,
                        "failureReason": None,
                    })
                else:
                    container_statuses = pod_log["status"].get(
                        "containerStatuses", [])
                    if container_statuses:
                        for container_status in container_statuses:

                            reason = container_status["state"]["waiting"]["reason"]
                            message = container_status["state"]["waiting"]["message"]
                            app_status_messages.append({
                                "status": "down",
                                "message": f"Pod:{index} is down. Message: {message}. ",
                                "failureReason": reason,
                                "replicaNumber": index
                            })
                    else:
                        app_status_messages.append({
                            "status": "failed",
                            "message": f"Failed to access pod status",
                            "failureReason": "unknown",
                            "replicaNumber": index
                        })

            app_list["pod_statuses"] = app_status_messages
            app_deployment_status_conditions = app_status_object.status.conditions

            app_list["image"] = app_status_object.spec.template.spec.containers[0].image
            app_list["port"] = app_status_object.spec.template.spec.containers[0].ports[0].container_port
            app_list["replicas"] = app_status_object.spec.replicas
            app_list["revision"] = app_status_object.metadata.annotations.get(
                'deployment.kubernetes.io/revision')

            # Get app command
            app_command = app_status_object.spec.template.spec.containers[0].command
            if app_command:
                app_list["command"] = ' '.join(app_command)
            else:
                app_list["command"] = app_command
            app_list["working_dir"] = app_status_object.spec.template.spec.containers[0].working_dir
            # Get environment variables
            env_list = app_status_object.spec.template.spec.containers[0].env
            envs = {}
            if not env_list:
                app_list["env_vars"] = env_list
            else:
                for item in env_list:
                    envs[item.name] = item.value
                app_list["env_vars"] = envs

            deployment_messages = []
            for deplyoment_status_condition in app_deployment_status_conditions:
                if deplyoment_status_condition.type == "Available":
                    app_deployment_status = deplyoment_status_condition.status
                deployment_messages.append(deplyoment_status_condition.message)

            app_list["deployment_messages"] = deployment_messages

            try:
                app_db_status_object = \
                    kube_client.appsv1_api.read_namespaced_deployment_status(
                        app_list['alias'] + "-postgres-db", project.alias)

                app_db_state_conditions = app_db_status_object.status.conditions

                for app_db_condition in app_db_state_conditions:
                    if app_db_condition.type == "Available":
                        app_db_status = app_db_condition.status

            except client.rest.ApiException:
                app_db_status = None
            if app.disabled:
                # Dont check status of disabled apps
                app_list['app_running_status'] = "disabled"
            elif app_deployment_status and not app_db_status:
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

            messages = [message.get("message")
                        for message in app_status_messages]
            reasons = [reason.get("failureReason")
                       for reason in app_status_messages]

            update_or_create_app_state(
                db.session, {
                    "status": app_list['app_running_status'],
                    "app": app_list['id'],
                    "failure_reason": ", ".join(reasons) if reasons else "",
                    "message": ", ".join(messages) if messages else "",
                    "last_check": datetime.datetime.now()
                }
            )

            # Get deployment version history
            version_history = kube_client.appsv1_api.list_namespaced_replica_set(
                project.alias, label_selector=f"app={app_list['alias']}")

            for item in version_history.items:
                # set revision_id basing on the current revision
                if app_list["revision"] == item.metadata.annotations.get('deployment.kubernetes.io/revision'):
                    app_list["revision_id"] = int(
                        item.metadata.creation_timestamp.timestamp())

            if errors:
                return dict(status='error', error=errors, data=dict(apps=app_list)), 409
            return dict(status='success', data=dict(apps=app_list)), 200

        except client.rest.ApiException as exc:

            if exc.status == 404:
                return dict(status='fail', data=json.loads(app_data), message="Application does not exist on the cluster"), 404

            return dict(status='fail', message=exc.reason), check_kube_error_code(exc.status)

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
                return dict(status='fail', message=f'app with id {app_id} not found'), 404

            project = app.project

            if not project:
                return dict(status='fail', message='Internal server error'), 500

            if not is_owner_or_admin(project, current_user_id, current_user_roles):
                if not is_authorised_project_user(project, current_user_id, 'admin'):
                    return dict(status='fail', message='Unauthorised'), 403

            cluster = project.cluster
            namespace = project.alias

            if not cluster or not namespace:
                log_activity('App', status='Failed',
                             operation='Delete',
                             description='Internal server error',
                             a_project_id=project.id,
                             a_cluster_id=project.cluster_id,
                             a_app_id=app_id)
                return dict(status='fail', message='Internal server error'), 500

            kube_host = cluster.host
            kube_token = cluster.token
            kube_client = create_kube_clients(kube_host, kube_token)

            # delete deployment and service for the app
            delete_cluster_app(kube_client, namespace, app)

            # delete the app from the database
            deleted = app.soft_delete()

            if not deleted:
                log_activity('App', status='Failed',
                             operation='Delete',
                             description='Internal server error',
                             a_project_id=project.id,
                             a_cluster_id=project.cluster_id,
                             a_app_id=app_id)
                return dict(status='fail', message='Internal server error'), 500

            log_activity('App', status='Success',
                         operation='Delete',
                         description=f'App {app_id} deleted successfully',
                         a_project_id=project.id,
                         a_cluster_id=project.cluster_id,
                         a_app_id=app_id)
            return dict(status='success', message=f'App {app_id} deleted successfully'), 200

        except client.rest.ApiException as e:
            return dict(status='fail', message=json.loads(e.body)), 500

        except Exception as e:
            return dict(status='fail', message=str(e)), 500

    @jwt_required
    def patch(self, app_id):

        app_schema = AppSchema(partial=True, exclude=["name"])

        update_data = request.get_json()

        validated_update_data, errors = app_schema.load(
            update_data, partial=True)

        if errors:
            return dict(status="fail", message=errors), 400

        app_image = validated_update_data.get('image', None)
        command = validated_update_data.get('command', None)
        env_vars = validated_update_data.get('env_vars', [])
        delete_env_vars = validated_update_data.get('delete_env_vars', [])
        replicas = validated_update_data.get('replicas', None)
        app_port = validated_update_data.get('port', None)
        private_repo = validated_update_data.get('private_image', False)
        docker_server = validated_update_data.get('docker_server', None)
        docker_username = validated_update_data.get('docker_username', None)
        docker_password = validated_update_data.get('docker_password', None)
        docker_email = validated_update_data.get('docker_email', None)
        custom_domain = validated_update_data.get('custom_domain', None)
        image_pull_secret = None

        try:
            current_user_id = get_jwt_identity()
            current_user_roles = get_jwt_claims()['roles']

            app = App.get_by_id(app_id)

            if not app:
                return dict(
                    status="fail",
                    message=f"App with id {app_id} not found"
                ), 404
            project = app.project

            if not project:
                return dict(status='fail', message='Internal server error'), 500

            if not is_owner_or_admin(project, current_user_id, current_user_roles):
                if not is_authorised_project_user(project, current_user_id, 'member'):
                    return dict(status='fail', message='Unauthorised'), 403

            cluster = project.cluster
            namespace = project.alias

            if not cluster or not namespace:
                log_activity('App', status='Failed',
                             operation='Update',
                             description='Internal server error',
                             a_project_id=project.id,
                             a_cluster_id=project.cluster_id,
                             a_app_id=app_id)
                return dict(status='fail', message='Internal server error'), 500

            kube_host = cluster.host
            kube_token = cluster.token

            kube_client = create_kube_clients(kube_host, kube_token)

            # Create a deployment object
            dep_name = f'{app.alias}-deployment'

            cluster_deployment = kube_client.appsv1_api.read_namespaced_deployment(
                name=dep_name,
                namespace=namespace
            )

            if app_image:
                if private_repo:
                    try:
                        app_secret = kube_client.kube.read_namespaced_secret(
                            namespace=namespace,
                            name=app.alias
                        )
                        # delete secret
                        kube_client.kube.delete_namespaced_secret(
                            name=app.alias,
                            namespace=namespace
                        )
                    except Exception as e:
                        if e.status != 404:
                            log_activity('App', status='Failed',
                                         operation='Update',
                                         description='Internal server error',
                                         a_project_id=project.id,
                                         a_cluster_id=project.cluster_id,
                                         a_app_id=app_id)
                            return dict(status='fail', message=str(e)), 500

                    # Create new secret
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
                        metadata=client.V1ObjectMeta(name=app.alias),
                        type='kubernetes.io/dockerconfigjson',
                        data={'.dockerconfigjson': str(secret_b64, "utf-8")})

                    kube_client.kube.create_namespaced_secret(
                        namespace=namespace,
                        body=secret_body,
                        _preload_content=False)

                    image_pull_secret = client.V1LocalObjectReference(
                        name=app.alias)
                    cluster_deployment.spec.template.spec.image_pull_secrets.append(
                        image_pull_secret)

                cluster_deployment.spec.template.spec.containers[0].image = app_image

            user = User.get_by_id(current_user_id)

            if custom_domain and user.is_beta_user:

                service_name = f'{app.alias}-service'
                ingress_name = f'{project.alias}-ingress'

                new_ingress_backend = client.V1IngressBackend(
                    service=client.V1IngressServiceBackend(
                        name=service_name,
                        port=client.V1ServiceBackendPort(
                            number=3000
                        )
                    )
                )

                new_ingress_rule = client.V1IngressRule(
                    host=custom_domain,
                    http=client.V1HTTPIngressRuleValue(
                        paths=[client.V1HTTPIngressPath(
                            path="",
                            path_type="ImplementationSpecific",
                            backend=new_ingress_backend
                        )]
                    )
                )

                ingress_list = kube_client.networking_api.list_namespaced_ingress(
                    namespace=namespace).items
                ingress = ingress_list[0]

                ingress.spec.rules.append(new_ingress_rule)

                kube_client.networking_api.patch_namespaced_ingress(
                    name=ingress_name,
                    namespace=namespace,
                    body=ingress
                )
                validated_update_data['url'] = f'https://{custom_domain}'
                validated_update_data['has_custom_domain'] = True

            if replicas:
                cluster_deployment.spec.replicas = replicas

            if app_port:
                cluster_deployment.spec.template.spec.containers[0].ports[0].container_port = app_port
                # get service
                service_name = f'{app.alias}-service'
                service = kube_client.kube.read_namespaced_service(
                    name=service_name,
                    namespace=namespace
                )

                if service:
                    service.spec.ports[0].target_port = app_port
                    kube_client.kube.replace_namespaced_service(
                        name=service_name,
                        namespace=namespace,
                        body=service
                    )

            if ("command" in validated_update_data and validated_update_data["command"] == ""):
                cluster_deployment.spec.template.spec.containers[0].command = [
                ]
            elif command is not None:
                cluster_deployment.spec.template.spec.containers[0].command = command.split(
                )

            if env_vars or delete_env_vars:
                update_app_env_vars(client, cluster_deployment,
                                    env_vars, delete_env_vars)

            # Update the application
            kube_client.appsv1_api.replace_namespaced_deployment(
                name=dep_name,
                namespace=namespace,
                body=cluster_deployment
            )

            # update the app in database
            updated_app = App.update(app, **validated_update_data)

            if not updated_app:
                log_activity('App', status='Failed',
                             operation='Update',
                             description='Internal server error',
                             a_project_id=project.id,
                             a_cluster_id=project.cluster_id,
                             a_app_id=app_id)
                return dict(
                    status='fail',
                    message='Internal Server Error'
                ), 500
            log_activity('App', status='Success',
                         operation='Update',
                         description=f'App {app_id} updated successfully',
                         a_project_id=project.id,
                         a_cluster_id=project.cluster_id,
                         a_app_id=app_id)
            return dict(
                status='success',
                message=f'App updated successfully'
            ), 200

        except client.rest.ApiException as exc:
            log_activity('App', status='Failed',
                         operation='Update',
                         description=exc.reason,
                         a_project_id=project.id,
                         a_cluster_id=project.cluster_id,
                         a_app_id=app_id)
            return dict(status='fail', message=exc.reason), check_kube_error_code(exc.status)

        except Exception as exc:
            log_activity('App', status='Failed',
                         operation='Update',
                         description=str(exc),
                         a_project_id=project.id,
                         a_cluster_id=project.cluster_id,
                         a_app_id=app_id)
            return dict(status='fail', message=str(exc)), 500


class AppRevisionsView(Resource):
    @jwt_required
    def get(self, app_id):
        """
        get application revisions
        """
        try:
            current_user_id = get_jwt_identity()
            current_user_roles = get_jwt_claims()['roles']

            # get pagination params
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 10, type=int)

            app_schema = AppSchema()

            app = App.get_by_id(app_id)

            if not app:
                return dict(status='fail', message=f'App {app_id} not found'), 404

            project = app.project

            if not project:
                return dict(status='fail', message='Internal server error'), 500

            if not is_owner_or_admin(project, current_user_id, current_user_roles):
                if not is_authorised_project_user(project, current_user_id, 'member'):
                    return dict(status='fail', message='Unauthorised'), 403

            app_data, errors = app_schema.dumps(app)

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
                    app_list['alias'] + "-deployment", project.alias)

            # this is needed in the subsequent executions to determine the current revision
            app_list["revision"] = app_status_object.metadata.annotations.get(
                'deployment.kubernetes.io/revision')

            # Get deployment version history
            version_history = kube_client.appsv1_api.list_namespaced_replica_set(
                project.alias, label_selector=f"app={app_list['alias']}")

            revisions = []
            for item in version_history.items:
                replica_command = item.spec.template.spec.containers[0].command
                if replica_command:
                    replica_command = ' '.join(replica_command)
                else:
                    replica_command = replica_command
                # TODO Add deployment status to replicas
                replica_set = {
                    'revision': item.metadata.annotations.get('deployment.kubernetes.io/revision'),
                    'revision_id': int(item.metadata.creation_timestamp.timestamp()),
                    'replicas': item.status.ready_replicas,
                    'created_at': str(item.metadata.creation_timestamp),
                    'image': item.spec.template.spec.containers[0].image,
                    'port': item.spec.template.spec.containers[0].ports[0].container_port,
                    'command': replica_command
                }

                if app_list["revision"] == item.metadata.annotations.get('deployment.kubernetes.io/revision'):
                    replica_set["current"] = True
                    app_list["revision_id"] = int(
                        item.metadata.creation_timestamp.timestamp())
                revisions.append(replica_set)

            # sort revisions
            revisions.sort(key=lambda x: x['revision_id'], reverse=True)

            # add pagination to these revisions
            pagination_meta_data, paginated_items = paginate(
                revisions, per_page=per_page, page=page)

            if errors:
                return dict(status='error', error=errors), 409
            return dict(status='success',
                        data=dict(pagination=pagination_meta_data, revisions=paginated_items)), 200

        except client.rest.ApiException as exc:

            if exc.status == 404:
                return dict(status='fail', data=json.loads(app_data), message="Application does not exist on the cluster"), 404

            return dict(status='fail', message=exc.reason), check_kube_error_code(exc.status)

        except Exception as exc:
            return dict(status='fail', message=str(exc)), 500


class AppRevertView(Resource):
    @jwt_required
    def patch(self, app_id):
        """
        revert app custom domain back to crane cloud domain
        """
        try:
            current_user_id = get_jwt_identity()
            current_user_roles = get_jwt_claims()['roles']

            app = App.get_by_id(app_id)

            if not app:
                return dict(
                    status="fail",
                    message=f"App with id {app_id} not found"
                ), 404
            project = app.project

            if not project:
                return dict(status='fail', message='Internal server error'), 500

            if not is_owner_or_admin(project, current_user_id, current_user_roles):
                if not is_authorised_project_user(project, current_user_id, 'admin'):
                    return dict(status='fail', message='Unauthorised'), 403

            cluster = project.cluster
            namespace = project.alias

            if not cluster or not namespace:
                return dict(status='fail', message='Internal server error'), 500

            app_sub_domain = get_app_subdomain(app.alias, cluster.sub_domain)
            custom_domain = None
            if type(app.url) is str:
                custom_domain = app.url.split("//", 1)[-1]

            if custom_domain == app_sub_domain:
                return dict(
                    status='fail',
                    message='App already has the crane cloud domain'
                ), 409

            # Create kube client
            kube_host = cluster.host
            kube_token = cluster.token

            kube_client = create_kube_clients(kube_host, kube_token)

            ingress_list = kube_client.networking_api.list_namespaced_ingress(
                namespace=namespace).items

            service_name = f'{app.alias}-service'
            ingress_name = f'{project.alias}-ingress'
            newUrl = None
            ingress = ingress_list[0]
            routes_list = ingress.spec.rules

            # Check if app subdomain is present in ingress list
            for item in routes_list:
                if item.host == app_sub_domain:
                    newUrl = app_sub_domain

            if not newUrl:
                # Create a new ingress rule with app Alias
                new_ingress_backend = client.V1IngressBackend(
                    service=client.V1IngressServiceBackend(
                        name=service_name,
                        port=client.V1ServiceBackendPort(
                            number=3000
                        )
                    )
                )

                new_ingress_rule = client.V1IngressRule(
                    host=app_sub_domain,
                    http=client.V1HTTPIngressRuleValue(
                        paths=[client.V1HTTPIngressPath(
                            path="",
                            path_type="ImplementationSpecific",
                            backend=new_ingress_backend
                        )]
                    )
                )

                ingress.spec.rules.append(new_ingress_rule)

            # Remove custom domain from ingress list
            for item in routes_list:
                if item.host == custom_domain:
                    ingress.spec.rules.remove(item)

            kube_client.networking_api.patch_namespaced_ingress(
                name=ingress_name,
                namespace=namespace,
                body=ingress
            )

            # Update the database with new url
            updated_app = App.update(
                app, url=f'https://{app_sub_domain}', has_custom_domain=False)

            if not updated_app:
                log_activity('App', status='Failed',
                             operation='Update',
                             description='App url revert Failed, Internal server error',
                             a_project_id=project.id,
                             a_cluster_id=project.cluster_id,
                             a_app_id=app_id)
                return dict(
                    status='fail',
                    message='Internal Server Error'
                ), 500
            log_activity('App', status='Success',
                         operation='Update',
                         description='App url reverted successfully',
                         a_project_id=project.id,
                         a_cluster_id=project.cluster_id,
                         a_app_id=app_id)
            return dict(
                status='success',
                message=f'App url reverted successfully'
            ), 200

        except client.rest.ApiException as exc:
            return dict(status='fail', message=exc.reason), check_kube_error_code(exc.status)

        except Exception as exc:
            return dict(status='fail', message=str(exc)), 500


class AppReviseView(Resource):
    @jwt_required
    def post(self, app_id, revision_id):
        """
        Revise app to a previous revision
        """
        try:
            current_user_id = get_jwt_identity()
            current_user_roles = get_jwt_claims()['roles']

            app = App.get_by_id(app_id)

            if not app:
                return dict(
                    status="fail",
                    message=f"App with id {app_id} not found"
                ), 404

            project = app.project

            if not project:
                return dict(status='fail', message='Internal server error'), 500

            if not is_owner_or_admin(project, current_user_id, current_user_roles):
                if not is_authorised_project_user(project, current_user_id, 'admin'):
                    return dict(status='fail', message='Unauthorised'), 403

            cluster = project.cluster
            namespace = project.alias

            if not cluster or not namespace:
                return dict(status='fail', message='Internal server error'), 500

            # Create kube client
            kube_host = cluster.host
            kube_token = cluster.token

            kube_client = create_kube_clients(kube_host, kube_token)

            # Get the app deployment
            dep_name = f'{app.alias}-deployment'
            deployment = kube_client.appsv1_api.read_namespaced_deployment(
                name=dep_name,
                namespace=namespace
            )

            if not deployment:
                log_activity('App', status='Failed',
                             operation='Update',
                             description=f'App revision Failed, Internal Server Error No project found',
                             a_project_id=project.id,
                             a_cluster_id=project.cluster_id,
                             a_app_id=app_id)
                return dict(
                    status='fail',
                    message='Internal Server Error, No project found'
                ), 500

            associated_replica_sets = kube_client.appsv1_api.list_namespaced_replica_set(
                namespace=namespace,
                label_selector=f'app={deployment.spec.template.metadata.labels["app"]}'
            )

            template = None

            for item in associated_replica_sets.items:
                revision = item.metadata.annotations['deployment.kubernetes.io/revision']
                if int(item.metadata.creation_timestamp.timestamp()) == int(revision_id):
                    template = item.spec.template

            if not template:
                log_activity('App', status='Failed',
                             operation='Update',
                             description=f'App revision Failed, Revision with id {revision_id} not found',
                             a_project_id=project.id,
                             a_cluster_id=project.cluster_id,
                             a_app_id=app_id)
                return dict(
                    status='fail',
                    message=f'Revision with id {revision_id} not found'
                ), 401

            patch = [
                {
                    'op': 'replace',
                    'path': '/spec/template',
                    'value': template
                },
                {
                    'op': 'replace',
                    'path': '/metadata/annotations',
                    'value': {
                        'deployment.kubernetes.io/revision': revision,
                        **deployment.metadata.annotations
                    }
                }
            ]

            kube_client.appsv1_api.patch_namespaced_deployment(
                body=patch,
                name=dep_name,
                namespace=namespace
            )
            log_activity('App', status='Successful',
                         operation='Update',
                         description='App revised successfully',
                         a_project_id=project.id,
                         a_cluster_id=project.cluster_id,
                         a_app_id=app_id)

            return dict(
                status='success',
                message=f'App revised successfully'
            ), 200

        except client.rest.ApiException as exc:
            log_activity('App', status='Failed',
                         operation='Update',
                         description=f'App revision Failed, {exc.reason}',
                         a_project_id=project.id,
                         a_cluster_id=project.cluster_id,
                         a_app_id=app_id)
            return dict(status='fail', message=exc.reason), check_kube_error_code(exc.status)

        except Exception as exc:
            log_activity('App', status='Failed',
                         operation='Update',
                         description=f'App revision Failed, {str(exc)}',
                         a_project_id=project.id,
                         a_cluster_id=project.cluster_id,
                         a_app_id=app_id)
            return dict(status='fail', message=str(exc)), 500


class AppRedeployView(Resource):
    @jwt_required
    def post(self, app_id):
        """
        Redeploy application
        """
        # TODO: handle private login
        app_schema = AppSchema()
        try:
            current_user_id = get_jwt_identity()
            current_user_roles = get_jwt_claims()['roles']

            app = App.get_by_id(app_id)

            if not app:
                return dict(
                    status="fail",
                    message=f"App with id {app_id} not found"
                ), 404

            project = app.project

            if not project:
                # todo: recreate project
                return dict(status='fail', message='Internal server error'), 500

            if not is_owner_or_admin(project, current_user_id, current_user_roles):
                if not is_authorised_project_user(project, current_user_id, 'admin'):
                    return dict(status='fail', message='Unauthorised'), 403

            user = User.get_by_id(current_user_id)

            cluster = project.cluster
            namespace = project.alias

            if not cluster or not namespace:
                return dict(status='fail', message='Internal server error'), 500

            kube_client = create_kube_clients(cluster.host, cluster.token)
            new_app = deploy_user_app(
                kube_client=kube_client,
                project=project,
                user=user,
                app=app
            )

            if type(new_app) == SimpleNamespace:
                status_code = new_app.status_code if new_app.status_code else 500
                return dict(status='fail', message=new_app.message), status_code

            new_app_data, _ = app_schema.dump(new_app)
            log_activity('App', status='Success',
                         operation='Create',
                         description='Redeployed app Successfully',
                         a_project_id=project.id,
                         a_cluster_id=project.cluster_id,
                         a_app_id=new_app.id)
            return dict(status='success', data=dict(app=new_app_data)), 201
        except Exception as e:
            log_activity('App', status='Failed',
                         operation='Create',
                         description=str(e),
                         a_project_id=project.id,
                         a_cluster_id=project.cluster_id,
                         )
            return dict(status='fail', message=str(e)), 500


class AppDockerWebhookListenerView(Resource):
    def post(self, app_id, user_id, tag):
        """
        Redeploy application from the Docker Hub webhook payload 
        """
        if not tag:
            tag = 'latest'
        payload = request.get_json()

        repository = payload['repository']['repo_name']

        app_image = f"{repository}:{tag}"
        # Get User
        user = User.get_by_id(user_id)
        if not user:
            logger.error(f"User with id {user_id} not found")
            return dict(
                status="fail",
                message=f"User with id {user} not found"
            ), 404

        # Get application
        app = App.get_by_id(app_id)
        if not app:
            logger.error(f"App with id {app_id} not found")
            return dict(
                status="fail",
                message=f"App with id {app_id} not found"
            ), 404

        # Get project
        project = app.project
        if not project:
            log_activity('App', status='Failed',
                         operation='Auto Update',
                         description=f'project for app {app_id} not found',
                         a_app_id=app.id)

            logger.error(
                f"App update for app id {app_id} is doesnot have a project")
            return dict(
                status="fail",
                message='Internal Server Error'
            ), 500
        user_roles = user.roles
        current_user_roles = [{'name': role.name} for role in user_roles]

        if not is_owner_or_admin(project, user_id, current_user_roles):
            if not is_authorised_project_user(project, user_id, 'admin'):
                return dict(status='fail', message='Unauthorised'), 403

        if app.disabled or app.project.disabled:
            logger.warning('app is disabled or project is disabled')
            return dict(
                status="fail",
                message=f"App with id {app_id} is disabled"
            ), 409

        try:

            cluster = project.cluster
            namespace = project.alias

            if not cluster or not namespace:
                log_activity('App', status='Failed',
                             operation='Auto Update',
                             description=f'{app_image}: Cluster or namespace not found',
                             a_project_id=project.id,
                             a_cluster_id=project.cluster_id,
                             a_app_id=app.id)
                logger.error('Cluster or namespace not found')
                return dict(
                    status='fail',
                    message="Internal Server Error"
                ), 500

            kube_host = cluster.host
            kube_token = cluster.token

            kube_client = create_kube_clients(kube_host, kube_token)

            dep_name = f'{app.alias}-deployment'

            cluster_deployment = kube_client.appsv1_api.read_namespaced_deployment(
                name=dep_name,
                namespace=namespace
            )
            if app.private_image:
                try:
                    app_secret = kube_client.kube.read_namespaced_secret(
                        namespace=namespace,
                        name=app.alias
                    )

                except Exception as e:
                    logger.exception('Exception occcured')
                    if e.status != 404:
                        log_activity('App', status='Failed',
                                     operation='Auto Update',
                                     description=f'{app_image}: Internal server error',
                                     a_project_id=project.id,
                                     a_cluster_id=project.cluster_id,
                                     a_app_id=app.id)

                cluster_deployment.spec.template.spec.image_pull_secrets.append(
                    app_secret)

            cluster_deployment.spec.template.spec.containers[0].image = app_image

            # Update the application image
            kube_client.appsv1_api.replace_namespaced_deployment(
                name=dep_name,
                namespace=namespace,
                body=cluster_deployment
            )

            # update the app in database
            updated_app = App.update(app, image=app_image)

            if not updated_app:
                log_activity('App', status='Failed',
                             operation='Auto Update',
                             description=f'{app_image}: Internal server error',
                             a_project_id=project.id,
                             a_cluster_id=project.cluster_id,
                             a_app_id=app.id)
                logger.error('Unable to update app in database')
                return dict(
                    status="fail",
                    message="Internal Server Error"
                ), 500

            log_activity('App', status='Success',
                         operation='Auto Update',
                         description=f'{app_image}: App {app.id} updated successfully',
                         a_project_id=project.id,
                         a_cluster_id=project.cluster_id,
                         a_app_id=app.id)
            return dict(
                status='success',
                message=f'Apps updated successfully'
            ), 200

        except Exception as e:
            logger.exception('Exception occcured')
            log_activity('App', status='Failed',
                         operation='Auto Update',
                         description=f'{app_image}: {str(e)}',
                         )
            return dict(status='fail', message=str(e)), 500


class AppDisableView(Resource):
    @jwt_required
    def post(self, app_id):

        # check credentials
        current_user_id = get_jwt_identity()
        current_user_roles = get_jwt_claims()['roles']

        app = App.get_by_id(app_id)
        if not app:
            return dict(status='fail', message=f'App with id {app_id} not found'), 404

        if not is_owner_or_admin(app.project, current_user_id, current_user_roles):
            if not is_authorised_project_user(app.project, current_user_id, 'admin'):
                return dict(status='fail', message='unauthorised'), 403

        if app.disabled:
            return dict(status='fail', message=f'App with id {app_id} is already disabled'), 409

        # Disable app
        disabled_app = disable_user_app(app, is_admin(current_user_roles))
        if type(disabled_app) == SimpleNamespace:
            status_code = disabled_app.status_code if disabled_app.status_code else 500
            return dict(status='fail', message=disabled_app.message), status_code

        return dict(status='success', message=f'App has been disabled successfully'), 201


class AppEnableView(Resource):
    @jwt_required
    def post(self, app_id):

        # check credentials
        current_user_id = get_jwt_identity()
        current_user_roles = get_jwt_claims()['roles']

        app = App.get_by_id(app_id)
        if not app:
            return dict(status='fail', message=f'App with id {app_id} not found'), 404

        if not is_owner_or_admin(app.project, current_user_id, current_user_roles):
            if not is_authorised_project_user(app.project, current_user_id, 'admin'):
                return dict(status='fail', message='unauthorised'), 403

        if app.project.disabled:
            return dict(status='fail', message=f'Apps project with id {app.project.id} is disabled, please enable it first'), 409

        if not app.disabled:
            return dict(status='fail', message=f'App with id {app_id} is already enabled'), 409

        # Prevent users from enabling admin disabled apps
        if app.admin_disabled and not is_admin(current_user_roles):
            return dict(status='fail', message=f'You are not authorised to disable App with id {app_id}, please contact an admin'), 403

        # Enable app
        enabled_app = enable_user_app(app)
        if type(enabled_app) == SimpleNamespace:
            status_code = enabled_app.status_code if enabled_app.status_code else 500
            return dict(status='fail', message=enabled_app.message), status_code

        return dict(status='success', message=f'App has been enabled successfully'), 201


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
            if not is_authorised_project_user(project, current_user_id, 'member'):
                return dict(status='fail', message='Unauthorised'), 403

        app_alias = app.alias
        namespace = project.alias

        if not project.cluster.prometheus_url:
            return dict(status='fail', message='No prometheus url provided'), 404

        os.environ["PROMETHEUS_URL"] = project.cluster.prometheus_url
        prometheus = Prometheus()

        prom_memory_data = prometheus.query_rang(
            start=start,
            end=end,
            step=step,
            metric='sum(rate(container_memory_usage_bytes{container_name!="POD", image!="",pod=~"' + app_alias + '.*", namespace="' + namespace + '"}[5m]))')

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
            if not is_authorised_project_user(project, current_user_id, 'member'):
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

        if not project.cluster.prometheus_url:
            return dict(status='fail', message='No prometheus url provided'), 404

        os.environ["PROMETHEUS_URL"] = project.cluster.prometheus_url
        prometheus = Prometheus()

        start = validated_query_data.get('start', yesterday.timestamp())
        end = validated_query_data.get('end', current_time.timestamp())
        step = validated_query_data.get('step', '1h')

        prom_data = prometheus.query_rang(
            start=start,
            end=end,
            step=step,
            metric='sum(rate(container_cpu_usage_seconds_total{container!="POD", image!="", namespace="' +
                   namespace + '", pod=~"' + app_alias + '.*"}[5m]))'
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
            if not is_authorised_project_user(project, current_user_id, 'member'):
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

        if not project.cluster.prometheus_url:
            return dict(status='fail', message='No prometheus url provided'), 404

        os.environ["PROMETHEUS_URL"] = project.cluster.prometheus_url
        prometheus = Prometheus()

        start = validated_query_data.get('start', yesterday.timestamp())
        end = validated_query_data.get('end', current_time.timestamp())
        step = validated_query_data.get('step', '1h')

        prom_data = prometheus.query_rang(
            start=start,
            end=end,
            step=step,
            metric='sum(rate(container_network_receive_bytes_total{namespace="' +
                   namespace + '", pod=~"' + app_alias + '.*"}[5m]))'
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
            if not is_authorised_project_user(project, current_user_id, 'member'):
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
            if type(state) == dict:
                waiting = state.get('waiting')
                if waiting:
                    try:
                        stop = state['waiting']['message'].index('container')
                        message = state['waiting']['message'][:stop]
                    except:
                        message = state['waiting'].get('message')

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
            if not is_authorised_project_user(project, current_user_id, 'member'):
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

        if not project.cluster.prometheus_url:
            return dict(status='fail', message='No prometheus url provided'), 404

        os.environ["PROMETHEUS_URL"] = project.cluster.prometheus_url
        prometheus = Prometheus()

        try:
            prom_data = prometheus.query(
                metric='sum(kube_persistentvolumeclaim_resource_requests_storage_bytes{namespace="' +
                       namespace + '", persistentvolumeclaim=~"' + app_alias + '.*"})'
            )
            #  change array values to json
            new_data = json.loads(prom_data)
            values = new_data["data"]

            percentage_data = prometheus.query(metric='100*(kubelet_volume_stats_used_bytes{namespace="' +
                                                      namespace + '", persistentvolumeclaim=~"' + app_alias + '.*"}/kubelet_volume_stats_capacity_bytes{namespace="' +
                                                      namespace + '", persistentvolumeclaim=~"' + app_alias + '.*"})'
                                               )

            data = json.loads(percentage_data)
            volume_perc_value = data["data"]
        except:
            return dict(status='fail', message='No values found'), 404

        return dict(status='success',
                    data=dict(storage_capacity=values, storage_percentage_usage=volume_perc_value)), 200


class AppDashboardView(Resource):
    pass
