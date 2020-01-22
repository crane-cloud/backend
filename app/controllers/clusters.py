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
        