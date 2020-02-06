import json
from flask_restful import Resource, request
from kubernetes import client
from app.schemas import ClusterSchema
from app.models.clusters import Cluster
from app.helpers.kube import create_kube_clients


class ClustersView(Resource):

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

            kube, extension_api, appsv1_api, api_client = create_kube_clients(kube_host, kube_token)

            # test connection by getting namespaces
            kube.list_namespace(_preload_content=False)

            new_cluster = Cluster(**validated_cluster_data)
            
            saved = new_cluster.save()

            if not saved:
                return dict(status='fail', message='Internal Server Error, possible duplicates'), 500

            new_cluster_data, errors = cluster_schema.dump(new_cluster)

            return dict(status='success', data=dict(cluster=new_cluster_data)), 201

        except Exception as e:
            return dict(status='fail', message='Connection to cluster failed'), 500

    def get(self):
        """
        """
        cluster_schema = ClusterSchema(many=True)

        clusters = Cluster.find_all()

        validated_cluster_data, errors = cluster_schema.dumps(clusters)

        if errors:
            return dict(status='fail', message='Internal Server Error'), 500

        return dict(status='Success',
                    data=dict(clusters=json.loads(validated_cluster_data))), 200


class ClusterDetailView(Resource):

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

            kube, extension_api, appsv1_api, api_client = create_kube_clients(kube_host, kube_token)

            # get number of nodes in the cluster
            node_count = len(kube.list_namespace().items)

            resource_count.append(dict(name='nodes', count=node_count))

            # get count of pvcs in the cluster
            pvc_count = len(kube.list_persistent_volume_claim_for_all_namespaces().items)

            resource_count.append(dict(name='PVCs', count=pvc_count))

            # get count of all pods in the cluster
            pod_count = len(kube.list_pod_for_all_namespaces().items)

            resource_count.append(dict(name='pods', count=pod_count))

            # get count of all services
            service_count = len(kube.list_service_for_all_namespaces().items)

            resource_count.append(dict(name='services', count=service_count))

            # get count of all deployments
            deployment_count = len(appsv1_api.list_deployment_for_all_namespaces().items)

            resource_count.append(dict(name='deployments', count=deployment_count))

            # get count of all namespaces in the cluster
            namespace_count = len(kube.list_namespace().items)

            resource_count.append(dict(name='namespaces', count=namespace_count))

            resource_count_json = json.dumps(resource_count)

            return dict(
                status='succcess',
                data=dict(
                    cluster=json.loads(validated_cluster_data),
                    resource_count=json.loads(resource_count_json))
                ), 200
        except Exception as e:
            return dict(status='fail', message=str(e)), 500

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

    def get(self, cluster_id):
        """
        """

        try:
            cluster_schema = ClusterSchema()

            cluster = Cluster.get_by_id(cluster_id)

            namespaces = []

            if not cluster:
                return dict(status='fail', message=f'cluster with id {cluster_id} does not exist'), 404

            kube_host = cluster.host
            kube_token = cluster.token

            kube, extension_api, appsv1_api, api_client = create_kube_clients(kube_host, kube_token)

            # get all namespaces in the cluster
            namespace_resp = kube.list_namespace()
            
            for item in namespace_resp.items:
                item = api_client.sanitize_for_serialization(item)
                namespaces.append(item)

            namespaces_json = json.dumps(namespaces)

            return dict(status='success', data=dict(namespaces=json.loads(namespaces_json))), 200
        except client.rest.ApiException as e:
            return dict(status='fail', message=e.reason), e.status

        except Exception as e:
            return dict(status='fail', message=str(e)), 500


class ClusterNamespaceDetailView(Resource):

    def get(self, cluster_id, namespace_name):
        """
        """

        try:

            cluster = Cluster.get_by_id(cluster_id)

            if not cluster:
                return dict(status='fail', message=f'cluster with id {cluster_id} does not exist'), 404

            kube_host = cluster.host
            kube_token = cluster.token

            kube, extension_api, appsv1_api, api_client = create_kube_clients(kube_host, kube_token)

            namespace = kube.read_namespace(name=namespace_name)
            namespace = api_client.sanitize_for_serialization(namespace)

            namespace_json = json.dumps(namespace)

            return dict(status='success', data=dict(namespace=json.loads(namespace_json))), 200

        except client.rest.ApiException as e:
            return dict(status='fail', message=e.reason), e.status

        except Exception as e:
            return dict(status='fail', message=str(e)), 500


class ClusterNodesView(Resource):

    def get(self, cluster_id):
        """
        """
        try:
            cluster = Cluster.get_by_id(cluster_id)

            nodes = []

            if not cluster:
                return dict(status='fail', message=f'cluster with id {cluster_id} does not exist'), 404

            kube_host = cluster.host
            kube_token = cluster.token

            kube, extension_api, appsv1_api, api_client = create_kube_clients(kube_host, kube_token)

            # get all nodes in the cluster
            node_resp = kube.list_node()

            for item in node_resp.items:
                item = api_client.sanitize_for_serialization(item)
                nodes.append(item)

            nodes_json = json.dumps(nodes)

            return dict(status='success', data=dict(nodes=json.loads(nodes_json))), 200
        except client.rest.ApiException as e:
            return dict(status='fail', message=e.reason), e.status

        except Exception as e:
            return dict(status='fail', message=str(e)), 500


class ClusterNodeDetailView(Resource):

    def get(self, cluster_id, node_name):
        """
        """
        try:
            cluster = Cluster.get_by_id(cluster_id)

            if not cluster:
                return dict(status='fail', message=f'cluster with id {cluster_id} does not exist'), 404

            kube_host = cluster.host
            kube_token = cluster.token

            kube, extension_api, appsv1_api, api_client = create_kube_clients(kube_host, kube_token)

            node = kube.read_node(name=node_name)
            node = api_client.sanitize_for_serialization(node)

            node_json = json.dumps(node)

            return dict(status='success', data=dict(node=json.loads(node_json))), 200

        except client.rest.ApiException as e:
            return dict(status='fail', message=e.reason), e.status

        except Exception as e:
            return dict(status='fail', message=str(e)), 500


class ClusterDeploymentsView(Resource):

    def get(self, cluster_id):
        """
        """
        try:
            cluster = Cluster.get_by_id(cluster_id)

            deployments = []

            if not cluster:
                return dict(status='fail', message=f'cluster with id {cluster_id} does not exist'), 404

            kube_host = cluster.host
            kube_token = cluster.token

            kube, extension_api, appsv1_api, api_client = create_kube_clients(kube_host, kube_token)

            deployment_resp = appsv1_api.list_deployment_for_all_namespaces()

            for item in deployment_resp.items:
                item = api_client.sanitize_for_serialization(item)
                deployments.append(item)

            deployments_json = json.dumps(deployments)

            return dict(status='success', data=dict(deployments=json.loads(deployments_json))), 200
        except client.rest.ApiException as e:
            return dict(status='fail', message=e.reason), e.status

        except Exception as e:
            return dict(status='fail', message=str(e)), 500


class ClusterDeploymentDetailView(Resource):

    def get(self, cluster_id, namespace_name, deployment_name):
        """
        """
        try:
            cluster = Cluster.get_by_id(cluster_id)

            if not cluster:
                return dict(status='fail', message=f'cluster with id {cluster_id} does not exist'), 404

            kube_host = cluster.host
            kube_token = cluster.token

            kube, extension_api, appsv1_api, api_client = create_kube_clients(kube_host, kube_token)

            deployment = appsv1_api.read_namespaced_deployment(deployment_name, namespace_name)
            deployment = api_client.sanitize_for_serialization(deployment)

            deployment_json = json.dumps(deployment)

            return dict(status='success', data=dict(deployment=json.loads(deployment_json))), 200

        except client.rest.ApiException as e:
            return dict(status='fail', message=e.reason), e.status

        except Exception as e:
            return dict(status='fail', message=str(e)), 500

class ClusterPvcsView(Resource):

    def get(self, cluster_id):
        """
        """
        try:
            cluster = Cluster.get_by_id(cluster_id)

            pvcs = []

            if not cluster:
                return dict(status='fail', message=f'cluster with id {cluster_id} does not exist'), 404

            kube_host = cluster.host
            kube_token = cluster.token

            kube, extension_api, appsv1_api, api_client = create_kube_clients(kube_host, kube_token)

            pvcs_resp = kube.list_persistent_volume_claim_for_all_namespaces()

            for item in pvcs_resp.items:
                item = api_client.sanitize_for_serialization(item)
                pvcs.append(item)

            pvcs_json = json.dumps(pvcs)

            return dict(status='success', data=dict(pvcs=json.loads(pvcs_json))), 200
        except client.rest.ApiException as e:
            return dict(status='fail', message=e.reason), e.status

        except Exception as e:
            return dict(status='fail', message=str(e)), 500


class ClusterPvcDetailView(Resource):

    def get(self, cluster_id, namespace_name, pvc_name):
        """
        """
        try:
            cluster = Cluster.get_by_id(cluster_id)

            if not cluster:
                return dict(status='fail', message=f'cluster with id {cluster_id} does not exist'), 404

            kube_host = cluster.host
            kube_token = cluster.token

            kube, extension_api, appsv1_api, api_client = create_kube_clients(kube_host, kube_token)

            pvc = kube.read_namespaced_persistent_volume_claim(pvc_name, namespace_name)
            pvc = api_client.sanitize_for_serialization(pvc)

            pvc_json = json.dumps(pvc)

            return dict(status='success', data=dict(pvc=json.loads(pvc_json))), 200

        except client.rest.ApiException as e:
            return dict(status='fail', message=e.reason), e.status

        except Exception as e:
            return dict(status='fail', message=str(e)), 500


class ClusterPVsView(Resource):

    def get(self, cluster_id):
        """
        """
        try:
            cluster = Cluster.get_by_id(cluster_id)

            pvs = []

            if not cluster:
                return dict(status='fail', message=f'cluster with id {cluster_id} does not exist'), 404

            kube_host = cluster.host
            kube_token = cluster.token

            kube, extension_api, appsv1_api, api_client = create_kube_clients(kube_host, kube_token)

            pvs_resp = kube.list_persistent_volume()

            for item in pvs_resp.items:
                item = api_client.sanitize_for_serialization(item)
                pvs.append(item)

            pvs_json = json.dumps(pvs)

            return dict(status='success', data=dict(pvs=json.loads(pvs_json))), 200
        except client.rest.ApiException as e:
            return dict(status='fail', message=e.reason), e.status

        except Exception as e:
            return dict(status='fail', message=str(e)), 500


class ClusterPVDetailView(Resource):

    def get(self, cluster_id, pv_name):
        """
        """
        try:
            cluster = Cluster.get_by_id(cluster_id)

            if not cluster:
                return dict(status='fail', message=f'cluster with id {cluster_id} does not exist'), 404

            kube_host = cluster.host
            kube_token = cluster.token

            kube, extension_api, appsv1_api, api_client = create_kube_clients(kube_host, kube_token)

            pv = kube.read_persistent_volume(pv_name)
            pv = api_client.sanitize_for_serialization(pv)

            pv_json = json.dumps(pv)

            return dict(status='success', data=dict(pv=json.loads(pv_json))), 200

        except client.rest.ApiException as e:
            return dict(status='fail', message=e.reason), e.status

        except Exception as e:
            return dict(status='fail', message=str(e)), 500


class ClusterPodsView(Resource):

    def get(self, cluster_id):
        """
        """
        try:
            cluster = Cluster.get_by_id(cluster_id)

            pods = []

            if not cluster:
                return dict(status='fail', message=f'cluster with id {cluster_id} does not exist'), 404

            kube_host = cluster.host
            kube_token = cluster.token

            kube, extension_api, appsv1_api, api_client = create_kube_clients(kube_host, kube_token)

            pods_resp = kube.list_pod_for_all_namespaces()

            for item in pods_resp.items:
                item = api_client.sanitize_for_serialization(item)
                pods.append(item)

            pods_json = json.dumps(pods)

            return dict(status='success', data=dict(pods=json.loads(pods_json))), 200
        except client.rest.ApiException as e:
            return dict(status='fail', message=e.reason), e.status

        except Exception as e:
            return dict(status='fail', message=str(e)), 500


class ClusterPodDetailView(Resource):

    def get(self, cluster_id, namespace_name, pod_name):
        """
        """
        try:
            cluster = Cluster.get_by_id(cluster_id)

            if not cluster:
                return dict(status='fail', message=f'cluster with id {cluster_id} does not exist'), 404

            kube_host = cluster.host
            kube_token = cluster.token

            kube, extension_api, appsv1_api, api_client = create_kube_clients(kube_host, kube_token)

            pod = kube.read_namespaced_pod(pod_name, namespace_name)
            pod = api_client.sanitize_for_serialization(pod)

            pod_json = json.dumps(pod)

            return dict(status='success', data=dict(pod=json.loads(pod_json))), 200

        except client.rest.ApiException as e:
            return dict(status='fail', message=e.reason), e.status

        except Exception as e:
            return dict(status='fail', message=str(e)), 500


class ClusterServicesView(Resource):

    def get(self, cluster_id):
        """
        """
        try:
            cluster = Cluster.get_by_id(cluster_id)

            services = []

            if not cluster:
                return dict(status='fail', message=f'cluster with id {cluster_id} does not exist'), 404

            kube_host = cluster.host
            kube_token = cluster.token

            kube, extension_api, appsv1_api, api_client = create_kube_clients(kube_host, kube_token)

            service_resp = kube.list_service_for_all_namespaces ()

            for item in service_resp.items:
                item = api_client.sanitize_for_serialization(item)
                services.append(item)

            services_json = json.dumps(services)

            return dict(status='success', data=dict(services=json.loads(services_json))), 200
        except client.rest.ApiException as e:
            return dict(status='fail', message=e.reason), e.status

        except Exception as e:
            return dict(status='fail', message=str(e)), 500


class ClusterServiceDetailView(Resource):

    def get(self, cluster_id, namespace_name, service_name):
        """
        """
        try:
            cluster = Cluster.get_by_id(cluster_id)

            if not cluster:
                return dict(status='fail', message=f'cluster with id {cluster_id} does not exist'), 404

            kube_host = cluster.host
            kube_token = cluster.token

            kube, extension_api, appsv1_api, api_client = create_kube_clients(kube_host, kube_token)

            service = kube.read_namespaced_service(service_name, namespace_name)
            service = api_client.sanitize_for_serialization(service)

            service_json = json.dumps(service)

            return dict(status='success', data=dict(deployment=json.loads(service_json))), 200

        except client.rest.ApiException as e:
            return dict(status='fail', message=e.reason), e.status

        except Exception as e:
            return dict(status='fail', message=str(e)), 500
