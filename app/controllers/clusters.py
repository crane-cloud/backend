import json
from flask_restful import Resource, request
from kubernetes import client
from flask_jwt_extended import jwt_required
from app.schemas import ClusterSchema
from app.models.clusters import Cluster
from app.helpers.kube import create_kube_clients
from app.helpers.decorators import admin_required
from app.helpers.pagination import paginate


class ClustersView(Resource):

    @admin_required
    def post(self):
        """
        """

        cluster_schema = ClusterSchema()

        cluster_data = request.get_json()

        validated_cluster_data, errors = cluster_schema.load(cluster_data)

        if errors:
            return dict(status='fail', message=errors), 400

        try:
            kube_host = validated_cluster_data['host']
            kube_token = validated_cluster_data['token']

            kube_client = create_kube_clients(kube_host, kube_token)

            # test connection by getting namespaces
            kube_client.kube.list_namespace(_preload_content=False)

            new_cluster = Cluster(**validated_cluster_data)

            saved = new_cluster.save()

            if not saved:
                return dict(status='fail', message='Internal Server Error, possible duplicates'), 500

            new_cluster_data, errors = cluster_schema.dump(new_cluster)

            return dict(status='success', data=dict(cluster=new_cluster_data)), 201

        except Exception:
            return dict(status='fail', message='Connection to cluster failed'), 500

    @jwt_required
    def get(self):
        """
        """
        cluster_schema = ClusterSchema(many=True)

        clusters = Cluster.find_all()

        validated_cluster_data, errors = cluster_schema.dumps(clusters)

        if errors:
            return dict(status='fail', message='Internal Server Error'), 500

        clusters_data_list = json.loads(validated_cluster_data)
        cluster_count = len(clusters_data_list)

        return dict(status='Success',
                    data=dict(clusters=json.loads(validated_cluster_data), metadata=dict(cluster_count=cluster_count))), 200


class ClusterDetailView(Resource):

    @admin_required
    def get(self, cluster_id):
        """
        """
        try:

            cluster_schema = ClusterSchema()

            resource_count = []

            cluster = Cluster.get_by_id(cluster_id)
            if not cluster:
                return dict(status='fail', message=f'Cluster with id {cluster_id} does not exist'), 404

            validated_cluster_data, errors = cluster_schema.dumps(cluster)

            if errors:
                return dict(status='fail', message=errors), 500

            kube_host = cluster.host
            kube_token = cluster.token

            kube_client = create_kube_clients(kube_host, kube_token)

            # get number of nodes in the cluster
            node_count = len(kube_client.kube.list_node().items)

            resource_count.append(dict(name='nodes', count=node_count))

            # get count of pvcs in the cluster
            pvc_count = len(
                kube_client.kube.list_persistent_volume_claim_for_all_namespaces().items)

            resource_count.append(dict(name='PVCs', count=pvc_count))

            # get count of all pods in the cluster
            pod_count = len(
                kube_client.kube.list_pod_for_all_namespaces().items)

            resource_count.append(dict(name='pods', count=pod_count))

            # get count of all services
            service_count = len(
                kube_client.kube.list_service_for_all_namespaces().items)

            resource_count.append(dict(name='services', count=service_count))

            # get count of all deployments
            deployment_count = len(
                kube_client.appsv1_api.list_deployment_for_all_namespaces().items)

            resource_count.append(
                dict(name='deployments', count=deployment_count))

            # get count of all namespaces in the cluster
            namespace_count = len(kube_client.kube.list_namespace().items)

            resource_count.append(
                dict(name='namespaces', count=namespace_count))

            resource_count_json = json.dumps(resource_count)

            return dict(
                status='succcess',
                data=dict(
                    cluster=json.loads(validated_cluster_data),
                    resource_count=json.loads(resource_count_json))
            ), 200

        except Exception as e:
            return dict(status='fail', message=str(e)), 500

    @admin_required
    def patch(self, cluster_id):
        """
        """

        cluster_schema = ClusterSchema(partial=True)

        new_cluster_data = request.get_json()

        validated_cluster_data, errors = cluster_schema.load(new_cluster_data)

        if errors:
            return dict(status='fail', messgae=errors), 400

        cluster = Cluster.get_by_id(cluster_id)

        if not cluster:
            return dict(status='fail', message=f'Cluster with id {cluster_id} does not exist'), 404

        cluster_updated = Cluster.update(cluster, **validated_cluster_data)

        if not cluster_updated:
            return dict(status='fail', message='Internal Server Error'), 500

        return dict(status='success', message='Cluster updated successfully'), 200

    @admin_required
    def delete(self, cluster_id):
        """
        """
        cluster = Cluster.get_by_id(cluster_id)

        if not cluster:
            return dict(status='fail', message='Cluster not found'), 404

        deleted = cluster.delete()

        if not deleted:
            return dict(status='fail', message='Internal Server Error'), 500

        return dict(status='success', message=f'Cluster with id {cluster_id} deleted successfully'), 200


class ClusterNamespacesView(Resource):

    @admin_required
    def get(self, cluster_id):
        """
        """

        try:
            cluster_schema = ClusterSchema()

            cluster = Cluster.get_by_id(cluster_id)

            if not cluster:
                return dict(status='fail', message=f'cluster with id {cluster_id} does not exist'), 404
            
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 10, type=int)

            kube_host = cluster.host
            kube_token = cluster.token

            kube_client = create_kube_clients(kube_host, kube_token)

            # get all namespaces in the cluster
            namespace_resp = kube_client.kube.list_namespace()

            pagination , paginated_items = paginate(namespace_resp , per_page , page)

            namespaces = []

            for item in paginated_items:
                item = kube_client.api_client.sanitize_for_serialization(item)
                namespaces.append(item)

            namespaces_json = json.dumps(namespaces)

            return dict(status='success', data=dict(pagination = pagination , namespaces=json.loads(namespaces_json))), 200
        except client.rest.ApiException as e:
            return dict(status='fail', message=e.reason), e.status

        except Exception as e:
            return dict(status='fail', message=str(e)), 500


class ClusterNamespaceDetailView(Resource):

    @admin_required
    def get(self, cluster_id, namespace_name):
        """
        """

        try:

            cluster = Cluster.get_by_id(cluster_id)

            if not cluster:
                return dict(
                    status='fail',
                    message=f'cluster with id {cluster_id} does not exist'
                ), 404

            kube_host = cluster.host
            kube_token = cluster.token

            kube_client = create_kube_clients(kube_host, kube_token)

            namespace = kube_client.kube.read_namespace(name=namespace_name)
            namespace = kube_client.api_client.sanitize_for_serialization(
                namespace)

            namespace_json = json.dumps(namespace)

            return dict(status='success', data=dict(namespace=json.loads(namespace_json))), 200

        except client.rest.ApiException as e:
            return dict(status='fail', message=e.reason), e.status

        except Exception as e:
            return dict(status='fail', message=str(e)), 500


class ClusterNodesView(Resource):

    @admin_required
    def get(self, cluster_id):
        """
        """
        try:
            cluster = Cluster.get_by_id(cluster_id)

            if not cluster:
                return dict(status='fail', message=f'cluster with id {cluster_id} does not exist'), 404
            
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 10, type=int)

            kube_host = cluster.host
            kube_token = cluster.token

            kube_client = create_kube_clients(kube_host, kube_token)

            # get all nodes in the cluster
            node_resp = kube_client.kube.list_node()

            pagination , paginated_items = paginate(node_resp , per_page , page)

            nodes = []

            for item in paginated_items:
                item = kube_client.api_client.sanitize_for_serialization(item)
                nodes.append(item)

            nodes_json = json.dumps(nodes)

            return dict(status='success', data=dict(pagination = pagination , nodes=json.loads(nodes_json))), 200
        except client.rest.ApiException as e:
            return dict(status='fail', message=e.reason), e.status

        except Exception as e:
            return dict(status='fail', message=str(e)), 500


class ClusterNodeDetailView(Resource):

    @admin_required
    def get(self, cluster_id, node_name):
        """
        """
        try:
            cluster = Cluster.get_by_id(cluster_id)

            if not cluster:
                return dict(status='fail', message=f'cluster with id {cluster_id} does not exist'), 404

            kube_host = cluster.host
            kube_token = cluster.token

            kube_client = create_kube_clients(kube_host, kube_token)

            node = kube_client.kube.read_node(name=node_name)
            node = kube_client.api_client.sanitize_for_serialization(node)

            node_json = json.dumps(node)

            return dict(status='success', data=dict(node=json.loads(node_json))), 200

        except client.rest.ApiException as e:
            return dict(status='fail', message=e.reason), e.status

        except Exception as e:
            return dict(status='fail', message=str(e)), 500


class ClusterDeploymentsView(Resource):

    @admin_required
    def get(self, cluster_id):
        """
        """
        try:
            cluster = Cluster.get_by_id(cluster_id)

            deployments = []

            if not cluster:
                return dict(status='fail', message=f'cluster with id {cluster_id} does not exist'), 404
            
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 10, type=int)

            kube_host = cluster.host
            kube_token = cluster.token

            kube_client = create_kube_clients(kube_host, kube_token)

            deployment_resp =\
                kube_client.appsv1_api.list_deployment_for_all_namespaces()
            
            pagination , paginated_items = paginate(deployment_resp.items , per_page , page)

            tot_deployment_count = 0
            tot_success_deployments = 0
            for item in paginated_items:
                item = kube_client.api_client.sanitize_for_serialization(item)
                deployments.append(item)

                if((item["status"]["conditions"][0]["status"] == "True") and (item["status"]["conditions"][1]["status"] == "True")):
                    tot_success_deployments = tot_success_deployments + 1

                tot_deployment_count = tot_deployment_count + 1

            tot_failed_deployments = tot_deployment_count - tot_success_deployments

            summary_stats_metadata = dict(total_deployment_count=tot_deployment_count,
                                          total_successful_deployments=tot_success_deployments, total_failed_deployment=tot_failed_deployments)
            deployments_json = json.dumps(deployments)

            return dict(status='success', data=dict(pagination = pagination , deployment_summary_stats=summary_stats_metadata, deployments=json.loads(deployments_json))), 200
        except client.rest.ApiException as e:
            return dict(status='fail', message=e.reason), e.status

        except Exception as e:
            return dict(status='fail', message=str(e)), 500


class ClusterDeploymentDetailView(Resource):

    @admin_required
    def get(self, cluster_id, namespace_name, deployment_name):
        """
        """
        try:
            cluster = Cluster.get_by_id(cluster_id)

            if not cluster:
                return dict(status='fail', message=f'cluster with id {cluster_id} does not exist'), 404

            kube_host = cluster.host
            kube_token = cluster.token

            kube_client = create_kube_clients(kube_host, kube_token)

            deployment = kube_client.appsv1_api.read_namespaced_deployment(
                deployment_name, namespace_name
            )

            deployment = kube_client.api_client.sanitize_for_serialization(
                deployment
            )

            deployment_json = json.dumps(deployment)

            return dict(
                status='success',
                data=dict(deployment=json.loads(deployment_json))
            ), 200

        except client.rest.ApiException as e:
            return dict(status='fail', message=e.reason), e.status

        except Exception as e:
            return dict(status='fail', message=str(e)), 500


class ClusterPvcsView(Resource):

    @admin_required
    def get(self, cluster_id):
        """
        """
        try:
            cluster = Cluster.get_by_id(cluster_id)

            if not cluster:
                return dict(status='fail', message=f'cluster with id {cluster_id} does not exist'), 404
            
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 10, type=int)

            kube_host = cluster.host
            kube_token = cluster.token

            kube_client = create_kube_clients(kube_host, kube_token)

            pvcs_resp = \
                kube_client.kube.list_persistent_volume_claim_for_all_namespaces()
            
            pagination , paginated_items = paginate(pvcs_resp.items , per_page , page)

            pvcs = []

            for item in paginated_items:
                item = kube_client.api_client.sanitize_for_serialization(item)
                pvcs.append(item)

            pvcs_json = json.dumps(pvcs)

            return dict(
                status='success', data=dict(pagination = pagination , pvcs=json.loads(pvcs_json))), 200

        except client.rest.ApiException as e:
            return dict(status='fail', message=e.reason), e.status

        except Exception as e:
            return dict(status='fail', message=str(e)), 500


class ClusterPvcDetailView(Resource):

    @admin_required
    def get(self, cluster_id, namespace_name, pvc_name):
        """
        """
        try:
            cluster = Cluster.get_by_id(cluster_id)

            if not cluster:
                return dict(status='fail', message=f'cluster with id {cluster_id} does not exist'), 404

            kube_host = cluster.host
            kube_token = cluster.token

            kube_client = create_kube_clients(kube_host, kube_token)

            pvc = kube_client.kube.read_namespaced_persistent_volume_claim(
                pvc_name, namespace_name
            )

            pvc = kube_client.api_client.sanitize_for_serialization(pvc)

            pvc_json = json.dumps(pvc)

            return dict(status='success', data=dict(pvc=json.loads(pvc_json))), 200

        except client.rest.ApiException as e:
            return dict(status='fail', message=e.reason), e.status

        except Exception as e:
            return dict(status='fail', message=str(e)), 500


class ClusterPVsView(Resource):

    @admin_required
    def get(self, cluster_id):
        """
        """
        try:
            cluster = Cluster.get_by_id(cluster_id)

            if not cluster:
                return dict(status='fail', message=f'cluster with id {cluster_id} does not exist'), 404
            
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 10, type=int)

            kube_host = cluster.host
            kube_token = cluster.token

            kube_client = create_kube_clients(kube_host, kube_token)

            pvs_resp = kube_client.kube.list_persistent_volume()

            pagination , paginated_items = paginate(pvs_resp.items , per_page , page)

            pvs = []

            for item in paginated_items:
                item = kube_client.api_client.sanitize_for_serialization(item)
                pvs.append(item)

            pvs_json = json.dumps(pvs)

            return dict(status='success', data=dict(pagination = pagination , pvs=json.loads(pvs_json))), 200

        except client.rest.ApiException as e:
            return dict(status='fail', message=e.reason), e.status

        except Exception as e:
            return dict(status='fail', message=str(e)), 500


class ClusterPVDetailView(Resource):

    @admin_required
    def get(self, cluster_id, pv_name):
        """
        """
        try:
            cluster = Cluster.get_by_id(cluster_id)

            if not cluster:
                return dict(
                    status='fail',
                    message=f'cluster with id {cluster_id} does not exist'
                ), 404

            kube_host = cluster.host
            kube_token = cluster.token

            kube_client = create_kube_clients(kube_host, kube_token)

            pv = kube_client.kube.read_persistent_volume(pv_name)
            pv = kube_client.api_client.sanitize_for_serialization(pv)

            pv_json = json.dumps(pv)

            return dict(status='success', data=dict(pv=json.loads(pv_json))), 200

        except client.rest.ApiException as e:
            return dict(status='fail', message=e.reason), e.status

        except Exception as e:
            return dict(status='fail', message=str(e)), 500


class ClusterPodsView(Resource):

    @admin_required
    def get(self, cluster_id):
        """
        """
        try:
            cluster = Cluster.get_by_id(cluster_id)

            if not cluster:
                return dict(
                    status='fail',
                    message=f'cluster with id {cluster_id} does not exist'
                ), 404
            
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 10, type=int)

            kube_host = cluster.host
            kube_token = cluster.token

            kube_client = create_kube_clients(kube_host, kube_token)
            pods_resp = kube_client.kube.list_pod_for_all_namespaces()
            
            pagination , paginated_items = paginate(pods_resp.items,per_page,page)

            pods = []

            for item in paginated_items:
                item = kube_client.api_client.sanitize_for_serialization(item)
                pods.append(item)

            return dict(status='success', data=dict(pagination=pagination , pods=pods)), 200

        except client.rest.ApiException as e:
            return dict(status='fail', message=e.reason), e.status

        except Exception as e:
            return dict(status='fail', message=str(e)), 500


class ClusterPodDetailView(Resource):

    @admin_required
    def get(self, cluster_id, namespace_name, pod_name):
        """
        """
        try:
            cluster = Cluster.get_by_id(cluster_id)

            if not cluster:
                return dict(status='fail', message=f'cluster with id {cluster_id} does not exist'), 404

            kube_host = cluster.host
            kube_token = cluster.token

            kube_client = create_kube_clients(kube_host, kube_token)

            pod = kube_client.kube.read_namespaced_pod(
                pod_name, namespace_name)
            pod = kube_client.api_client.sanitize_for_serialization(pod)

            pod_json = json.dumps(pod)

            return dict(status='success', data=dict(pod=json.loads(pod_json))), 200

        except client.rest.ApiException as e:
            return dict(status='fail', message=e.reason), e.status

        except Exception as e:
            return dict(status='fail', message=str(e)), 500


class ClusterServicesView(Resource):

    @admin_required
    def get(self, cluster_id):
        """
        """
        try:
            cluster = Cluster.get_by_id(cluster_id)

            if not cluster:
                return dict(
                    status='fail',
                    message=f'cluster with id {cluster_id} does not exist'
                ), 404
            
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 10, type=int)

            kube_host = cluster.host
            kube_token = cluster.token

            kube_client = create_kube_clients(kube_host, kube_token)

            service_resp =\
                kube_client.kube.list_service_for_all_namespaces()
            
            pagination , paginated_items = paginate(service_resp.items,per_page,page)

            services = []

            for item in paginated_items:
                item = kube_client.api_client.sanitize_for_serialization(item)
                services.append(item)

            services_json = json.dumps(services)

            return dict(status='success', data=dict(pagination = pagination , services=json.loads(services_json))), 200

        except client.rest.ApiException as e:
            return dict(status='fail', message=e.reason), e.status

        except Exception as e:
            return dict(status='fail', message=str(e)), 500


class ClusterServiceDetailView(Resource):

    @admin_required
    def get(self, cluster_id, namespace_name, service_name):
        """
        """
        try:
            cluster = Cluster.get_by_id(cluster_id)

            if not cluster:
                return dict(status='fail', message=f'cluster with id {cluster_id} does not exist'), 404

            kube_host = cluster.host
            kube_token = cluster.token

            kube_client = create_kube_clients(kube_host, kube_token)

            service = kube_client.kube.read_namespaced_service(
                service_name, namespace_name)
            service = kube_client.api_client.sanitize_for_serialization(
                service)

            service_json = json.dumps(service)

            return dict(status='success', data=dict(service=json.loads(service_json))), 200

        except client.rest.ApiException as e:
            return dict(status='fail', message=e.reason), e.status

        except Exception as e:
            return dict(status='fail', message=str(e)), 500


class ClusterJobsView(Resource):

    @admin_required
    def get(self, cluster_id):
        """
        """
        try:
            cluster = Cluster.get_by_id(cluster_id)

            jobs = []

            if not cluster:
                return dict(status='fail', message=f'cluster with id {cluster_id} does not exist'), 404

            kube_host = cluster.host
            kube_token = cluster.token

            kube_client = create_kube_clients(kube_host, kube_token)

            jobs_resp = kube_client.batchv1_api.list_job_for_all_namespaces()

            for item in jobs_resp.items:
                item = kube_client.api_client.sanitize_for_serialization(item)
                jobs.append(item)

            jobs_json = json.dumps(jobs)

            return dict(status='success', data=dict(jobs=json.loads(jobs_json))), 200

        except client.rest.ApiException as e:
            return dict(status='fail', message=e.reason), e.status

        except Exception as e:
            return dict(status='fail', message=str(e)), 500


class ClusterJobDetailView(Resource):

    @admin_required
    def get(self, cluster_id, namespace_name, job_name):
        """
        """
        try:
            cluster = Cluster.get_by_id(cluster_id)

            if not cluster:
                return dict(status='fail', message=f'cluster with id {cluster_id} does not exist'), 404

            kube_host = cluster.host
            kube_token = cluster.token

            kube_client = create_kube_clients(kube_host, kube_token)

            job = kube_client.batchv1_api.read_namespaced_job(
                job_name, namespace_name)

            job = kube_client.api_client.sanitize_for_serialization(job)

            job_json = json.dumps(job)

            return dict(status='success', data=dict(job=json.loads(job_json))), 200

        except client.rest.ApiException as e:
            return dict(status='fail', message=e.reason), e.status

        except Exception as e:
            return dict(status='fail', message=str(e)), 500


class ClusterStorageClassView(Resource):

    @admin_required
    def get(self, cluster_id):
        """
        """
        try:
            cluster = Cluster.get_by_id(cluster_id)

            storage_classes = []

            if not cluster:
                return dict(
                    status='fail',
                    message=f'cluster with id {cluster_id} does not exist'
                ), 404

            kube_host = cluster.host
            kube_token = cluster.token

            kube_client = create_kube_clients(kube_host, kube_token)

            storage_classes_resp = kube_client.storageV1Api.list_storage_class()

            for item in storage_classes_resp.items:
                item = kube_client.api_client.sanitize_for_serialization(item)
                storage_classes.append(item)

            storage_classes_json = json.dumps(storage_classes)

            return dict(
                status='success',
                data=dict(storage_classes=json.loads(storage_classes_json))
            ), 200

        except client.rest.ApiException as e:
            return dict(status='fail', message=e.reason), e.status

        except Exception as e:
            return dict(status='fail', message=str(e)), 500


class ClusterStorageClassDetailView(Resource):

    @admin_required
    def get(self, cluster_id, storage_class_name):
        """
        """
        try:
            cluster = Cluster.get_by_id(cluster_id)

            if not cluster:
                return dict(
                    status='fail',
                    message=f'cluster with id {cluster_id} does not exist'
                ), 404

            kube_host = cluster.host
            kube_token = cluster.token

            kube_client = create_kube_clients(kube_host, kube_token)

            storage_class =\
                kube_client.storageV1Api.read_storage_class(storage_class_name)

            storage_class =\
                kube_client.api_client.sanitize_for_serialization(
                    storage_class)

            storage_class_json = json.dumps(storage_class)

            return dict(
                status='success',
                data=dict(storage_class=json.loads(storage_class_json))
            ), 200

        except client.rest.ApiException as e:
            return dict(status='fail', message=e.reason), e.status

        except Exception as e:
            return dict(status='fail', message=str(e)), 500
