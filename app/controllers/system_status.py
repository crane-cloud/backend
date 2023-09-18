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
        postgres_database_count = ProjectDatabase.query.filter(ProjectDatabase.database_flavour_name == 'postgres').count()
        return dict(status='success' , data={
            'Users' : {
                'total_count' : user_count,
                'verified' : verified_users,
                'beta_users' : beta_users
            },
            'Projects' : {
                'total_count' : project_count,
                'disabled' : disabled_projects
            },
            'Apps' : {
                'total_count' : app_count,
            },
            'Databases' : {
                'total_count' : database_count,
                'mysql' : mysql_database_count,
                'postgres' : postgres_database_count
            }
        }) , 200




