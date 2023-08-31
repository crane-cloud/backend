
import os
from flask_restful import Resource
from sqlalchemy import null
from app.controllers.statuses import get_client_status_infor, get_cluster_status_info, get_database_status_infor, get_prometheus_status_info
from app.models.clusters import Cluster
from flask import request
from app.helpers.decorators import admin_required
from app.models.user import User
from app.models.project import Project
from app.models.app import App
from app.models.project_database import ProjectDatabase


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
             'url': os.getenv('MIRA_FRONTEND_URL', None)},
            {'name': 'mira-backend',
             'url': os.getenv('MIRA_BACKEND_URL', None)},
        ]
        mira_status = get_client_status_infor(mira_apps_list)
        return dict(status='success', data={
            'cranecloud_status': cranecloud_status,
            'clusters_status': clusters_status,
            'prometheus_status': prometheus_status,
            'database_status': database_status,
            'mira_status': mira_status
        }), 200


class SystemSummaryView(Resource):

    @admin_required
    def get(self):

        # Users 
        user_count = User.query.count()
        verified_users = User.query.filter(User.verified==True).count()
        beta_users = User.query.filter(User.is_beta_user==True).count()

        #Projects
        project_count = Project.query.count()
        disabled_projects = Project.query.filter(Project.disabled == True).count()

        #apps
        app_count = App.query.count()


        #Databases
        database_count = ProjectDatabase.query.count()
        mysql_database_count = ProjectDatabase.query.filter(ProjectDatabase.database_flavour_name == 'mysql').count()


        return dict(status='success' , data={
            'Users' : {
                'total_count' : user_count,
                'verified' : verified_users,
                'beta_users' : beta_users
            },
            'Projects' : {
                'total_count' : project_count,
                'active' : active_projects
            },
            'Apps' : {
                'total_count' : app_count,
            },
            'Databases' : {
                'total_count' : database_count,
                'mysql' : mysql_database_count,
                'postgres' : database_count - mysql_database_count 
            }
        }) , 200