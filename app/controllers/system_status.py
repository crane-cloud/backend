
from flask_restful import Resource
from app.helpers.kube import get_cluster_status_info
from app.models.clusters import Cluster


class SystemStatusView(Resource):

    def get(self):
        # get clusters status
        clusters = Cluster.find_all()
        clusters_status = {'clusters': get_cluster_status_info(clusters)}
        print(clusters_status)

        return dict(status='success', data=clusters_status), 200
