import os
from app.helpers.cost_modal import CostModal
from app.helpers.alias import create_alias
from app.helpers.admin import is_owner_or_admin, is_current_or_admin
from app.helpers.role_search import has_role
from app.helpers.kube import create_kube_clients, delete_cluster_app
from app.models.billing_invoice import BillingInvoice
from app.models.user import User
from app.models.clusters import Cluster
from app.models.project import Project
from app.schemas import ProjectSchema, MetricsSchema
import datetime
from prometheus_http_client import Prometheus
import json
from flask_restful import Resource, request
from kubernetes import client
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt_claims
from app.helpers.db_flavor import get_db_flavour
from app.schemas.monitoring_metrics import BillingMetricsSchema


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

                saved = project.save()

                if not saved:
                    # delete the namespace
                    kube_client.kube.delete_namespace(namespace_name)
                    return dict(
                        status='fail',
                        message='Internal Server Error'), 500

            # create a billing invoice on project creation
            new_invoice = BillingInvoice(project_id=project.id)

            saved_new_invoice = new_invoice.save()

            if not saved_new_invoice:
                return dict(
                    status='fail',
                    message='An error occured during creation of a new invoice record'), 400

            new_project_data, errors = project_schema.dump(project)

            return dict(status='success', data=dict(project=new_project_data)), 201

        except client.rest.ApiException as e:
            return dict(status='fail', message=str(e.body)), e.status

        except Exception as err:
            return dict(status='fail', message=str(err)), 500

    @jwt_required
    def get(self):
        """
        """

        current_user_id = get_jwt_identity()
        current_user_roles = get_jwt_claims()['roles']

        project_schema = ProjectSchema(many=True)

        if has_role(current_user_roles, 'administrator'):
            projects = Project.find_all()
        else:
            projects = Project.find_all(owner_id=current_user_id)

        project_data, errors = project_schema.dumps(projects)

        if errors:
            return dict(status='fail', message=errors), 500

        return dict(status='success', data=dict(projects=json.loads(project_data))), 200


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
            return dict(status='fail', message='unauthorised'), 403

        project_data, errors = project_schema.dumps(project)

        if errors:
            return dict(status='fail', message=errors), 500

        return dict(status='success', data=dict(
            project=json.loads(project_data))), 200

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
                        return dict(
                            status="fail",
                            message=f"Database flavour with name {database.database_flavour_name} is not mysql or postgres."
                        ), 409

                    # Delete the database
                    database_service = db_flavour['class']
                    database_connection = database_service.check_db_connection()

                    if not database_connection:
                        return dict(
                            status="fail",
                            message=f"Failed to connect to the database service"
                        ), 500

                    delete_database = database_service.delete_database(
                        database.name)

                    if not delete_database:
                        return dict(
                            status="fail",
                            message=f"Unable to delete database"
                        ), 500

                    # Delete database record from database
                    deleted_database = database.delete()

                    if not deleted_database:
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
                    deleted = app.delete()

            # get corresponding namespace
            try:
                namespace = kube_client.kube.read_namespace(project.alias)
                # delete namespace if it exists
                if namespace:
                    kube_client.kube.delete_namespace(project.alias)
            except Exception as e:
                # if unable to get namespace, it means it is already deleted
                pass

            # To do; change delete to a soft delete
            deleted = project.delete()

            if not deleted:
                return dict(status='fail', message='deletion failed'), 500

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
                        deleted = app.delete()

                deleted = project.delete()

                if not deleted:
                    return dict(status='fail', message='deletion failed'), 500

                return dict(
                    status='success',
                    message=f'project {project_id} deleted successfully'
                ), 200

            return dict(status='fail', message=e.reason), e.status

        except Exception as e:
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
                return dict(status='fail', message='unauthorised'), 403

            updated = Project.update(project, **validate_project_data)

            if not updated:
                return dict(status='fail', message='internal server error'), 500

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
