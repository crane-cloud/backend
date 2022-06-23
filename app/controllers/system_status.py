
from flask_restful import Resource
from sqlalchemy import null
from app.controllers.statuses import get_client_status_infor, get_cluster_status_info, get_database_status_infor, get_prometheus_status_info
from app.models.clusters import Cluster


class SystemStatusView(Resource):

    def get(self):
        # get cranecloud status
        cranecloud_status = get_client_status_infor()
        # get clusters status
        clusters = Cluster.find_all()
        clusters_status = None
        prometheus_status = None
        if clusters:
            clusters_status = get_cluster_status_info(clusters)
            prometheus_status = get_prometheus_status_info(clusters)
        database_status = get_database_status_infor()
        return dict(status='success', data={
            'cranecloud_status': cranecloud_status,
            'clusters_status': clusters_status,
            'prometheus_status': prometheus_status,
            'database_status': database_status
        }), 200
