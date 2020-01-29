import json
from flask_restful import Resource, request
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

            kube, extension_api, appsv1_api = create_kube_clients(kube_host, kube_token)

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

        cluster_schema = ClusterSchema()

        cluster = Cluster.get_by_id(cluster_id)

        if not cluster:
            return dict(status='fail', message=f'Cluster with id {cluster_id} does not exist'), 404

        validated_cluster_data, errors = cluster_schema.dumps(cluster)

        if errors:
            return dict(status='fail', message=errors), 500

        return dict(status='succcess', data=dict(cluster=json.loads(validated_cluster_data))), 200

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
