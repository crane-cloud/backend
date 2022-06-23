
import os
from flask_restful import Resource
from sqlalchemy import null
from app.controllers.statuses import get_client_status_infor, get_cluster_status_info, get_database_status_infor, get_prometheus_status_info
from app.models.clusters import Cluster
from flask import request


class SystemStatusView(Resource):

    def get(self):
        # get cranecloud status
        front_end_url = os.getenv('CLIENT_BASE_URL', None)
        apps_list = [
            {'name': 'cranecloud-frontend', 'url': front_end_url},
            {'name': 'cranecloud-backend', 'url': request.url_root},
        ]
        cranecloud_status = get_client_status_infor(apps_list)

        # get clusters status
        clusters = Cluster.find_all()
        clusters_status = None
        prometheus_status = None
        if clusters:
            clusters_status = get_cluster_status_info(clusters)
            prometheus_status = get_prometheus_status_info(clusters)

        # get database status
        database_status = get_database_status_infor()

        # get MIRA status
        mira_apps_list = [
            {'name': 'mira-frontend',
             'url': 'http://mira.cranecloud.io:3000'},
            {'name': 'mira-backend',
             'url': 'http://mira.cranecloud.io:3000'},
        ]
        mira_status = get_client_status_infor(mira_apps_list)
        return dict(status='success', data={
            'cranecloud_status': cranecloud_status,
            'clusters_status': clusters_status,
            'prometheus_status': prometheus_status,
            'database_status': database_status,
            'mira_status': mira_status
        }), 200
