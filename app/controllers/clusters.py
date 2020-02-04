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

            return dict(status='Success', data=dict(namespaces=json.loads(namespaces_json))), 200
        except client.rest.ApiException as e:
            return dict(status='fail', message=e.reason), e.status


class ClusterNamespaceDetailView(Resource):

    def get(self, cluster_id, namespace_name):
        """
        """

        try:
            cluster_schema = ClusterSchema()

            cluster = Cluster.get_by_id(cluster_id)

            if not cluster:
                return dict(status='fail', message=f'cluster with id {cluster_id} does not exist'), 404

            kube_host = cluster.host
            kube_token = cluster.token

            kube, extension_api, appsv1_api, api_client = create_kube_clients(kube_host, kube_token)

            namespace = kube.read_namespace(name=namespace_name)
            namespace = api_client.sanitize_for_serialization(namespace)

            namespace_json = json.dumps(namespace)

            return dict(status='Success', data=dict(namespace=json.loads(namespace_json))), 200

        except client.rest.ApiException as e:
            return dict(status='fail', message=e.reason), e.status



