import os
import datetime
import json
from app.helpers.cost_modal import CostModal
from app.helpers.alias import create_alias
from app.helpers.admin import is_authorised_project_user, is_owner_or_admin, is_current_or_admin, is_admin
from app.helpers.role_search import has_role
from app.helpers.activity_logger import log_activity
from app.helpers.kube import create_kube_clients, delete_cluster_app, disable_user_app, enable_user_app
from app.models.billing_invoice import BillingInvoice
from app.models.project_users import ProjectUser
from app.models.user import User
from app.models.clusters import Cluster
from app.models.project import Project
from app.schemas import ProjectSchema, MetricsSchema, AppSchema, ProjectDatabaseSchema, ProjectUserSchema
from app.helpers.decorators import admin_required
import datetime
from prometheus_http_client import Prometheus
from flask_restful import Resource, request
from kubernetes import client
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt_claims
from app.helpers.db_flavor import get_db_flavour
from app.schemas.monitoring_metrics import BillingMetricsSchema
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import or_, func
from app.models.project_database import ProjectDatabase


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
                message=f'project with name {validated_project_data["name"]} already exists'
            ), 409
        try:
            validated_project_data['alias'] =\
                create_alias(validated_project_data['name'])
            namespace_name = validated_project_data['alias']
            cluster_id = validated_project_data['cluster_id']
            cluster = Cluster.get_by_id(cluster_id)

            if not cluster:
                return dict(
                    status='fail',
                    message=f'cluster {cluster_id} not found'
                ), 404

            kube_host = cluster.host
            kube_token = cluster.token

            kube_client = create_kube_clients(kube_host, kube_token)

            # create namespace in cluster
            cluster_namespace = kube_client.kube.create_namespace(
                client.V1Namespace(
                    metadata=client.V1ObjectMeta(name=namespace_name)
                ))

            # create project in database
            if cluster_namespace:

                ingress_name = f"{validated_project_data['alias']}-ingress"

                ingress_meta = client.V1ObjectMeta(
                    name=ingress_name
                )

                ingress_default_rule = client.V1IngressRule(
                    host="traefik-ui.cranecloud.io",
                    http=client.V1HTTPIngressRuleValue(
                        paths=[client.V1HTTPIngressPath(
                            path="/*",
                            path_type="ImplementationSpecific",
                            backend=client.V1IngressBackend(
                                service=client.V1IngressServiceBackend(
                                    name="traefik-web-ui-ext",
                                    port=client.V1ServiceBackendPort(
                                        number=80
                                    )
                                )
                            )
                        )]
                    )
                )

                ingress_spec = client.V1IngressSpec(
                    rules=[ingress_default_rule]
                )

                ingress_body = client.V1Ingress(
                    metadata=ingress_meta,
                    spec=ingress_spec
                )

                kube_client.networking_api.create_namespaced_ingress(
                    namespace=namespace_name,
                    body=ingress_body
                )

                project = Project(**validated_project_data)

                # Add user as owner of project
                new_role = ProjectUser(
                    role="owner",
                    user_id=project.owner_id
                )
                project.users.append(new_role)

            saved = project.save()

            if not saved:
                log_activity('Project', status='Failed',
                             operation='Create',
                             description="Internal Server Error",
                             a_cluster_id=cluster_id)

                # delete the namespace
                kube_client.kube.delete_namespace(namespace_name)

                return dict(status="fail", message="Internal Server Error"), 500

            # create a billing invoice on project creation
            new_invoice = BillingInvoice(project_id=project.id)

            saved_new_invoice = new_invoice.save()

            if not saved_new_invoice:
                return dict(
                    status='fail',
                    message='An error occured during creation of a new invoice record'), 400

            # create a billing invoice on project creation
            new_invoice = BillingInvoice(project_id=project.id)

            saved_new_invoice = new_invoice.save()

            if not saved_new_invoice:
                return dict(
                    status='fail',
                    message='An error occured during creation of a new invoice record'), 400

            # create a billing invoice on project creation
            new_invoice = BillingInvoice(project_id=project.id)

            saved_new_invoice = new_invoice.save()

            if not saved_new_invoice:
                return dict(
                    status='fail',
                    message='An error occured during creation of a new invoice record'), 400

            new_project_data, errors = project_schema.dump(project)
            log_activity('Project', status='Success',
                         operation='Create',
                         description='Created project Successfully',
                         a_project_id=project.id,
                         a_cluster_id=cluster_id)

            return dict(status='success', data=dict(project=new_project_data)), 201

        except client.rest.ApiException as e:
            log_activity('Project', status='Failed',
                         operation='Create',
                         description=e.body,
                         a_cluster_id=cluster_id)
            return dict(status='fail', message=str(e.body)), e.status

        except Exception as err:
            log_activity('Project', status='Failed',
                         operation='Create',
                         description=err.body,
                         a_cluster_id=cluster_id)
            return dict(status='fail', message=str(err)), 500

    @jwt_required
    def get(self):
        """
        """

        current_user_id = get_jwt_identity()
        current_user_roles = get_jwt_claims()['roles']
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        keywords = request.args.get('keywords', '')
        disabled = request.args.get('disabled')
        project_type = request.args.get('project_type')

        project_schema = ProjectSchema(many=True)
        projects = []
        pagination_data = {}

        filter_mapping = {
            'disabled': disabled,
            'project_type': project_type
        }

        # count items per project category
        project_metadata = {}
        for category in filter_mapping.keys():
            distinct_counts = Project.query.with_entities(getattr(Project, category), func.count(
                getattr(Project, category))).group_by(getattr(Project, category)).all()
            if category == 'disabled':
                project_metadata[category] = distinct_counts[0][1] if distinct_counts else 0
            else:
                project_metadata[category] = dict(distinct_counts)

        # Identify which attribute to filter on
        attribute, attribute_value = next(
            ((k, v) for k, v in filter_mapping.items() if v), (None, None))

        if has_role(current_user_roles, 'administrator'):

            if (keywords == ''):
                if attribute:
                    paginated = (Project.query.filter(getattr(Project, attribute) == attribute_value).order_by(
                        Project.date_created.desc()).paginate(page=page, per_page=per_page, error_out=False))
                    projects = paginated.items
                    pagination_data = {
                        'total': paginated.total,
                        'pages': paginated.pages,
                        'page': paginated.page,
                        'per_page': paginated.per_page,
                        'next': paginated.next_num,
                        'prev': paginated.prev_num
                    }

                else:
                    paginated = Project.find_all(
                        paginate=True, page=page, per_page=per_page)
                    projects = paginated.items
                    pagination_data = paginated.pagination
            else:
                paginated = Project.query.filter(Project.name.ilike('%'+keywords+'%')).order_by(Project.date_created.desc()).paginate(
                    page=page, per_page=per_page, error_out=False)
                projects = paginated.items
                pagination_data = {
                    'total': paginated.total,
                    'pages': paginated.pages,
                    'page': paginated.page,
                    'per_page': paginated.per_page,
                    'next': paginated.next_num,
                    'prev': paginated.prev_num
                }
        else:
            try:

                if (keywords == ''):
                    if attribute:
                        paginated = (Project.query.filter(getattr(Project, attribute) == attribute_value).order_by(
                            Project.date_created.desc()).paginate(page=page, per_page=per_page, error_out=False))
                        projects = paginated.items
                        pagination = {
                            'total': paginated.total,
                            'pages': paginated.pages,
                            'page': paginated.page,
                            'per_page': paginated.per_page,
                            'next': paginated.next_num,
                            'prev': paginated.prev_num
                        }
                    else:
                        pagination = Project.query.filter(or_(Project.owner_id == current_user_id, Project.users.any(
                            ProjectUser.user_id == current_user_id))).order_by(Project.date_created.desc()).paginate(
                            page=page, per_page=per_page, error_out=False)
                else:

                    pagination = Project.query.filter(Project.owner_id == current_user_id, Project.name.ilike('%'+keywords+'%'), Project.users.any(
                        ProjectUser.user_id == current_user_id)).order_by(Project.date_created.desc()).paginate(
                        page=page, per_page=per_page, error_out=False)

                projects = pagination.items
                if pagination:
                    pagination_data = {
                        'total': pagination.total,
                        'pages': pagination.pages,
                        'page': pagination.page,
                        'per_page': pagination.per_page,
                        'next': pagination.next_num,
                        'prev': pagination.prev_num
                    }
            except SQLAlchemyError:
                pagination = None
                return dict(status='fail', message='Internal Server Error'), 500

        project_data, errors = project_schema.dumps(projects)

        if errors:
            return dict(status='fail', message=errors), 500

        # Updating user's last login
        user = User.get_by_id(current_user_id)
        user.last_seen = datetime.datetime.now()
        user.save()
        # ADD a logger for when user.save does not work

        return dict(status='success',
                    data=dict(
                        metadata=project_metadata,
                        pagination=pagination_data,
                        projects=json.loads(project_data))), 200


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
            return dict(
                status='fail',
                message=f'project {project_id} not found'
            ), 404

        if not is_owner_or_admin(project, current_user_id, current_user_roles):
            if not is_authorised_project_user(project, current_user_id, 'member'):
                return dict(status='fail', message='unauthorised'), 403

        project_data, errors = project_schema.dumps(project)
        if errors:
            return dict(status='fail', message=errors), 500

        # if user not an admin
        if not is_admin(current_user_roles):
            return dict(status='success', data=dict(
                project=json.loads(project_data))), 200
        else:
            apps_schema = AppSchema(many=True)
            database_schema = ProjectDatabaseSchema(many=True)
            users_schema = ProjectUserSchema(many=True)
            apps = project.apps
            databases = project.project_databases
            users = project.users
            apps_data, errors = apps_schema.dumps(apps)
            databases_data, errors = database_schema.dumps(databases)
            users_data, errors = users_schema.dumps(users)
            return dict(status='success', data=dict(
                project=dict(**json.loads(project_data),
                             apps=json.loads(apps_data),
                             databases=json.loads(databases_data),
                             users=json.loads(users_data)))), 200

    @jwt_required
    def delete(self, project_id):
        """
        """

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

        try:
            # check for dbs in project and delete them from host and CC db
            databases_list = project.project_databases

            if databases_list:
                for database in databases_list:

                    database_flavour_name = database.database_flavour_name
                    if not database_flavour_name:
                        database_flavour_name = "mysql"

                    db_flavour = get_db_flavour(database_flavour_name)

                    if not db_flavour:
                        message = f"Database flavour with name {database.database_flavour_name} is not mysql or postgres."
                        log_activity('Project', status='Failed',
                                     operation='Delete',
                                     description=message,
                                     a_project_id=project_id,
                                     a_database_id=database.id,
                                     a_cluster_id=project.cluster_id)
                        return dict(
                            status="fail",
                            message=message
                        ), 409

                    # Delete the database
                    database_service = db_flavour['class']
                    database_connection = database_service.check_db_connection()

                    if not database_connection:
                        log_activity('Project', status='Failed',
                                     operation='Delete',
                                     description='Failed to connect to database service',
                                     a_project_id=project_id,
                                     a_database_id=database.id,
                                     a_cluster_id=project.cluster_id)
                        return dict(
                            status="fail",
                            message=f"Failed to connect to the database service"
                        ), 500

                    delete_database = database_service.delete_database(
                        database.name)

                    if not delete_database:
                        log_activity('Project', status='Failed',
                                     operation='Delete',
                                     description='Unable to delete database',
                                     a_project_id=project_id,
                                     a_database_id=database.id,
                                     a_cluster_id=project.cluster_id)
                        return dict(
                            status="fail",
                            message=f"Unable to delete database"
                        ), 500

                    # Delete database record from database
                    deleted_database = database.soft_delete()

                    if not deleted_database:
                        log_activity('Project', status='Failed',
                                     operation='Delete',
                                     description='Internal server error',
                                     a_project_id=project_id,
                                     a_database_id=database.id,
                                     a_cluster_id=project.cluster_id)
                        return dict(status='fail', message=f'Internal Server Error'), 500

            # get cluster for the project
            cluster = Cluster.get_by_id(project.cluster_id)

            if not cluster:
                return dict(status='fail', message='cluster not found'), 500

            kube_host = cluster.host
            kube_token = cluster.token

            kube_client = create_kube_clients(kube_host, kube_token)

            # check and delete apps within a project
            apps_list = project.apps
            if apps_list:
                for app in apps_list:
                    delete_cluster_app(kube_client, project.alias, app)
                    # delete the app from the database
                    deleted = app.soft_delete()

            # get corresponding namespace
            try:
                namespace = kube_client.kube.read_namespace(project.alias)
                # delete namespace if it exists
                if namespace:
                    kube_client.kube.delete_namespace(project.alias)
            except Exception as e:
                # if unable to get namespace, it means it is already deleted
                pass

            deleted = project.soft_delete()

            if not deleted:
                log_activity('Project', status='Failed',
                             operation='Delete',
                             description='Internal server error',
                             a_project_id=project_id,
                             a_cluster_id=project.cluster_id)
                return dict(status='fail', message='deletion failed'), 500

            log_activity('Project', status='Success',
                         operation='Delete',
                         description='Deleted project Successfully',
                         a_project_id=project.id,
                         a_cluster_id=project.cluster_id)
            return dict(
                status='success',
                message=f'project {project_id} deleted successfully'
            ), 200

        except client.rest.ApiException as e:
            if e.status == 404:
                """
                deletes apps and project from db if not found on the cluster
                """
                apps_list = project.apps
                if apps_list:
                    for app in apps_list:
                        # delete the app from the database
                        deleted = app.soft_delete()

                deleted = project.soft_delete()

                if not deleted:
                    return dict(status='fail', message='deletion failed'), 500
                log_activity('Project', status='Success',
                             operation='Delete',
                             description='Deleted project Successfully',
                             a_project_id=project.id,
                             a_cluster_id=project.cluster_id)
                return dict(
                    status='success',
                    message=f'project {project_id} deleted successfully'
                ), 200
            log_activity('Project', status='Failed',
                         operation='Delete',
                         description=e.reason,
                         a_project_id=project_id,
                         a_cluster_id=project.cluster_id)
            return dict(status='fail', message=e.reason), e.status

        except Exception as e:
            log_activity('Project', status='Failed',
                         operation='Delete',
                         description=str(e),
                         a_project_id=project_id,
                         a_cluster_id=project.cluster_id)
            return dict(status='fail', message=str(e)), 500

    @jwt_required
    def patch(self, project_id):
        """
        """

        try:
            current_user_id = get_jwt_identity()
            current_user_roles = get_jwt_claims()['roles']

            project_schema = ProjectSchema(
                only=("name", "description", "organisation", "project_type"), partial=True)

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
                    message=f'project with name {validate_project_data["name"]} already exists'
                ), 409

            project = Project.get_by_id(project_id)

            if not project:
                return dict(status='fail', message=f'Project {project_id} not found'), 404

            if not is_owner_or_admin(project, current_user_id, current_user_roles):
                if not is_authorised_project_user(project, current_user_id, 'admin'):
                    return dict(status='fail', message='unauthorised'), 403

            updated = Project.update(project, **validate_project_data)

            if not updated:
                log_activity('Project', status='Failed',
                             operation='Update',
                             description='Internal Server Error',
                             a_project_id=project.id,
                             a_cluster_id=project.cluster_id
                             )
                return dict(status='fail', message='internal server error'), 500

            log_activity('Project', status='Success',
                         operation='Update',
                         description='Updated project Successfully',
                         a_project_id=project.id,
                         a_cluster_id=project.cluster_id)
            return dict(
                status='success',
                message=f'project {project_id} updated successfully'
            ), 200

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

        return dict(
            status='success',
            data=dict(projects=json.loads(projects_json))
        ), 200


class ClusterProjectsView(Resource):

    @admin_required
    def get(self, cluster_id):
        """
        Get projects in a cluster
        """

        current_user_roles = get_jwt_claims()['roles']
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)

        if not is_admin(current_user_roles):
            return dict(status='fail', message='user unauthorised'), 403

        project_schema = ProjectSchema(many=True)
        cluster = Cluster.get_by_id(cluster_id)

        if not cluster:
            return dict(status='fail', message=f'Cluster with id {cluster_id} not found'), 404

        projects = cluster.projects
        projects = Project.find_all(
            cluster_id=cluster_id, paginate=True, page=page, per_page=per_page)

        projects_json, errors = project_schema.dumps(projects.items)

        if errors:
            return dict(status='fail', message='Internal server error'), 500

        return dict(
            status='success',
            data=dict(
                pagination=projects.pagination,
                projects=json.loads(projects_json))
        ), 200


class ProjectMemoryUsageView(Resource):

    @jwt_required
    def post(self, project_id):

        project_memory_schema = MetricsSchema()
        project_query_data = request.get_json()

        validated_query_data, errors = project_memory_schema.load(
            project_query_data)

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

        if not is_owner_or_admin(project, current_user_id, current_user_roles):
            if not is_authorised_project_user(project, current_user_id, 'member'):
                return dict(status='fail', message='unauthorised'), 403

        namespace = project.alias
        if not project.cluster.prometheus_url:
            return dict(status='fail', message='No prometheus url provided'), 404

        os.environ["PROMETHEUS_URL"] = project.cluster.prometheus_url
        prometheus = Prometheus()

        prom_memory_data = prometheus.query_rang(
            start=start,
            end=end,
            step=step,
            metric='sum(rate(container_memory_usage_bytes{container_name!="POD", image!="", namespace="'+namespace+'"}[5m]))')

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


class ProjectCPUView(Resource):
    @jwt_required
    def post(self, project_id):
        current_user_id = get_jwt_identity()
        current_user_roles = get_jwt_claims()['roles']

        project_memory_schema = MetricsSchema()
        project_cpu_data = request.get_json()

        validated_query_data, errors = project_memory_schema.load(
            project_cpu_data)

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

        # Get current time
        current_time = datetime.datetime.now()
        yesterday = current_time + datetime.timedelta(days=-1)
        namespace = project.alias

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
            metric='sum(rate(container_cpu_usage_seconds_total{container!="POD", image!="",namespace="' +
            namespace+'"}[5m]))'
        )

        #  change array values to json"values"
        new_data = json.loads(prom_data)
        cpu_data_list = []

        try:
            for value in new_data["data"]["result"][0]["values"]:
                case = {'timestamp': value[0], 'value': value[1]}
                cpu_data_list.append(case)
        except:
            return dict(status='fail', message='No values found'), 404

        return dict(status='success', data=dict(values=cpu_data_list)), 200


class ProjectNetworkRequestView(Resource):
    @jwt_required
    def post(self, project_id):
        current_user_id = get_jwt_identity()
        current_user_roles = get_jwt_claims()['roles']

        project_network_schema = MetricsSchema()
        project_network_data = request.get_json()

        validated_query_data, errors = project_network_schema.load(
            project_network_data)

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

        # Get current time
        current_time = datetime.datetime.now()
        yesterday = current_time + datetime.timedelta(days=-1)
        namespace = project.alias

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
            namespace+'"}[5m]))'
        )
        #  change array values to json"values"
        new_data = json.loads(prom_data)
        network_data_list = []

        try:
            for value in new_data["data"]["result"][0]["values"]:
                case = {'timestamp': float(value[0]), 'value': float(value[1])}
                network_data_list.append(case)
        except:
            return dict(status='fail', message='No values found'), 404

        return dict(status='success', data=dict(values=network_data_list)), 200


class ProjectStorageUsageView(Resource):
    @jwt_required
    def post(self, project_id):

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

        namespace = project.alias

        if not project.cluster.prometheus_url:
            return dict(status='fail', message='No prometheus url provided'), 404

        os.environ["PROMETHEUS_URL"] = project.cluster.prometheus_url
        prometheus = Prometheus()

        try:
            prom_data = prometheus.query(metric='sum(kube_persistentvolumeclaim_resource_requests_storage_bytes{namespace="' +
                                         namespace+'"})'
                                         )
            #  change array values to json
            new_data = json.loads(prom_data)
            values = new_data["data"]

            percentage_data = prometheus.query(metric='sum(100*(kubelet_volume_stats_used_bytes{namespace="' +
                                               namespace+'"}/kubelet_volume_stats_capacity_bytes{namespace="' +
                                               namespace+'"}))'
                                               )

            data = json.loads(percentage_data)
            volume_perc_value = data["data"]
        except:
            return dict(status='fail', message='No values found'), 404

        return dict(status='success', data=dict(storage_capacity=values, storage_percentage_usage=volume_perc_value)), 200


class ProjectGetCostsView(Resource):
    @jwt_required
    def post(self, project_id):
        current_user_id = get_jwt_identity()
        current_user_roles = get_jwt_claims()['roles']

        project_billing_schema = BillingMetricsSchema()
        project_billing_data = request.get_json()

        validated_query_data, errors = project_billing_schema.load(
            project_billing_data)

        project = Project.get_by_id(project_id)

        if not project:
            return dict(
                status='fail',
                message=f'project {project_id} not found'
            ), 404

        if not is_owner_or_admin(project, current_user_id, current_user_roles):
            return dict(status='fail', message='unauthorised'), 403

        creation_timestamp = int(project.date_created.timestamp())

        # TODO: Have start date begin from last bill payment date
        start = validated_query_data.get('start', creation_timestamp)
        end = validated_query_data.get(
            'end', int(datetime.datetime.now().timestamp()))
        series = validated_query_data.get('series', False)
        show_deployments = validated_query_data.get('show_deployments', False)

        if show_deployments:
            series = False
        window = validated_query_data.get('window', None)

        if not window:
            window = f'{start},{end}'

        namespace = project.alias
        # namespace = 'liqo'
        cost_url = project.cluster.cost_modal_url

        if not cost_url:
            return dict(status='fail', message='No cost modal url provided, please contact your administrator'), 404

        cost_modal = CostModal(cost_url)

        cost_data = cost_modal.get_namespace_cost(
            window, namespace, series=series, show_deployments=show_deployments)

        if cost_data is False:
            return dict(status='fail', message='Error occurred'), 500

        return dict(status='success', data=dict(cost_data=cost_data)), 200


class ProjectDisableView(Resource):
    @jwt_required
    def post(self, project_id):

        # check credentials
        current_user_id = get_jwt_identity()
        current_user_roles = get_jwt_claims()['roles']

        project = Project.get_by_id(project_id)
        if not project:
            return dict(status='fail', message=f'Project with id {project_id} not found'), 404

        if not is_owner_or_admin(project, current_user_id, current_user_roles):
            if not is_authorised_project_user(project, current_user_id, 'admin'):
                return dict(status='fail', message='unauthorised'), 403

        if project.disabled:
            return dict(status='fail', message=f'Project with id {project_id} is already disabled'), 409

        # get postgres project databases
        db_flavour = 'postgres'
        psql_project_databases = ProjectDatabase.find_all(
            project_id=project_id, database_flavour_name=db_flavour)

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
                return dict(
                    status="fail",
                    message=f"Failed to connect to the database service"
                ), 500

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
                        return dict(
                            status="fail",
                            message=f"Unable to disable database"
                        ), 500
                    database.disabled = True
                    database.save()

        # get mysql project databases
        db_flavour = 'mysql'
        mysql_project_databases = ProjectDatabase.find_all(
            project_id=project_id, database_flavour_name=db_flavour)

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
                return dict(
                    status="fail",
                    message=f"Failed to connect to the database service"
                ), 500

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
                        return dict(
                            status="fail",
                            message=f"Unable to disable database"
                        ), 500
                    database.disabled = True
                    database.save()

        # Disable apps
        try:
            kube_host = project.cluster.host
            kube_token = project.cluster.token

            kube_client = create_kube_clients(kube_host, kube_token)

            # scale apps down to 0
            for app in project.apps:
                disable_user_app(app)

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
            project.save()

            log_activity('Project', status='Success',
                         operation='Disable',
                         description='Disabled project Successfully',
                         a_project_id=project.id,
                         a_cluster_id=project.cluster_id)
            return dict(
                status='success',
                message=f'project {project_id} disabled successfully'
            ), 200

        except client.rest.ApiException as e:
            log_activity('Project', status='Failed',
                         operation='Disable',
                         description='Error disabling application',
                         a_project_id=project.id,
                         a_cluster_id=project.cluster_id)
            return dict(status='fail', message=str(e.body)), e.status

        except Exception as err:
            log_activity('Project', status='Failed',
                         operation='Disable',
                         description=err.body,
                         a_project_id=project.id,
                         a_cluster_id=project.cluster_id)
            return dict(status='fail', message=str(err)), 500


class ProjectEnableView(Resource):
    @jwt_required
    def post(self, project_id):

        # check credentials
        current_user_id = get_jwt_identity()
        current_user_roles = get_jwt_claims()['roles']

        project = Project.get_by_id(project_id)
        if not project:
            return dict(status='fail', message=f'Project with id {project_id} not found'), 404

        if not is_owner_or_admin(project, current_user_id, current_user_roles):
            if not is_authorised_project_user(project, current_user_id, 'admin'):
                return dict(status='fail', message='unauthorised'), 403

        if project.admin_disabled:
            return dict(status='fail', message=f'Project with id {project_id} is admin disabled'), 409

        if not project.disabled:
            return dict(status='fail', message=f'Project with id {project_id} is already enabled'), 409

        # get postgres project databases
        db_flavour = 'postgres'
        psql_project_databases = ProjectDatabase.find_all(
            project_id=project_id, database_flavour_name=db_flavour)

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
                return dict(
                    status="fail",
                    message=f"Failed to connect to the database service"
                ), 500

            # Enable the postgres databases
            for database in psql_project_databases:

                # check if disabled
                if database.disabled:

                    disable_database = database_service.enable_user_log_in(
                        database.user)

                    if not disable_database:
                        log_activity('Database', status='Failed',
                                     operation='Disable',
                                     description='Unable to disable postgres database, Internal Server Error',
                                     a_project_id=project.id,
                                     a_cluster_id=project.cluster_id)
                        return dict(
                            status="fail",
                            message=f"Unable to disable database"
                        ), 500
                    database.disabled = False
                    database.save()

        # get mysql project databases
        db_flavour = 'mysql'
        mysql_project_databases = ProjectDatabase.find_all(
            project_id=project_id, database_flavour_name=db_flavour)

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
                return dict(
                    status="fail",
                    message=f"Failed to connect to the database service"
                ), 500

            # Enable mysql databases
            for database in mysql_project_databases:

                # check if disabled
                if database.disabled:

                    disable_database = database_service.enable_user_log_in(
                        database.user, database.password)

                    if not disable_database:
                        log_activity('Database', status='Failed',
                                     operation='Disable',
                                     description='Unable to disable mysql database, Internal Server Error',
                                     a_project_id=project.id,
                                     a_cluster_id=project.cluster_id
                                     )
                        return dict(
                            status="fail",
                            message=f"Unable to Enable database"
                        ), 500
                    database.disabled = False
                    database.save()

        # Disable apps
        try:
            kube_host = project.cluster.host
            kube_token = project.cluster.token

            kube_client = create_kube_clients(kube_host, kube_token)
            try:
                # scale apps down to 0
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
                    return dict(status='fail', message=str(e.body)), e.status\


            # save project
            project.disabled = False
            project.save()

            log_activity('Project', status='Success',
                         operation='Enable',
                         description='Enabled project Successfully',
                         a_project_id=project.id,
                         a_cluster_id=project.cluster_id)
            return dict(
                status='success',
                message=f'project {project_id} Enabled successfully'
            ), 200

        except Exception as err:
            log_activity('Project', status='Failed',
                         operation='Enable',
                         description=err.body,
                         a_project_id=project.id,
                         a_cluster_id=project.cluster_id)
            return dict(status='fail', message=str(err)), 500

