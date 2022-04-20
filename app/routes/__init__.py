from flask_restful import Api
from app.controllers import (
    IndexView, UsersView, UserLoginView, OAuthView, DeploymentsView, RolesView,
    RolesDetailView, UserRolesView, UserDataSummaryView, ClustersView,
    ClusterDetailView, ClusterNamespacesView,
    ClusterNamespaceDetailView, ClusterNodesView, ClusterNodeDetailView,
    ClusterDeploymentsView, ClusterDeploymentDetailView, ClusterPvcsView, ClusterPvcDetailView,
    ClusterPVDetailView, ClusterPVsView, ClusterPodsView, ClusterPodDetailView,
    ClusterServiceDetailView, ClusterServicesView, ClusterJobsView, ClusterJobDetailView,
    ClusterStorageClassView, ClusterStorageClassDetailView,
    ProjectsView, ProjectDetailView, UserProjectsView, UserEmailVerificationView,
    EmailVerificationRequest, ForgotPasswordView, ResetPasswordView, AppsView, UserDetailView, AdminLoginView,
    ProjectAppsView, AppDetailView, RegistriesView, ProjectMemoryUsageView, ProjectCPUView, AppMemoryUsageView,
    AppCpuUsageView, AppNetworkUsageView, ProjectNetworkRequestView, AppLogsView, AppStorageUsageView, ProjectStorageUsageView,
    ProjectDatabaseView, ProjectDatabaseDetailView, ProjectDatabaseAdminView, ProjectDatabaseAdminDetailView,
    ProjectDatabaseResetView, ProjectDatabaseAdminResetView, ProjectDatabasePasswordResetView, ProjectDatabaseAdminPasswordResetView,
    ProjectDatabaseRetrievePasswordView, ProjectDatabaseAdminRetrievePasswordView, DatabaseStatsView, AppDataSummaryView,
    UserAdminUpdateView, AppRevertView, TransactionRecordView)
from app.controllers.transactions import TransactionRecordDetailView


api = Api()

# Index route
api.add_resource(IndexView, '/')

# User routes
api.add_resource(UsersView, '/users', endpoint='users')
api.add_resource(UserLoginView, '/users/login', endpoint='login')
api.add_resource(AdminLoginView, '/users/admin_login', endpoint='admin_login')
api.add_resource(UserEmailVerificationView, '/users/verify/<string:token>')
api.add_resource(EmailVerificationRequest, '/users/verify')
api.add_resource(ForgotPasswordView, '/users/forgot_password')
api.add_resource(ResetPasswordView, '/users/reset_password/<string:token>')
api.add_resource(UserDetailView, '/users/<string:user_id>')
api.add_resource(OAuthView, '/users/oauth')
api.add_resource(UserDataSummaryView, '/users/summary')
api.add_resource(UserAdminUpdateView, '/users/admin_update')


# Deployments
api.add_resource(DeploymentsView, '/deployments', endpoint='deployments')

# Clusters
api.add_resource(ClustersView, '/clusters', endpoint='clusters')
api.add_resource(ClusterDetailView, '/clusters/<string:cluster_id>')
api.add_resource(ClusterNamespacesView,
                 '/clusters/<string:cluster_id>/namespaces')
api.add_resource(ClusterNamespaceDetailView,
                 '/clusters/<string:cluster_id>/namespaces/<string:namespace_name>')
api.add_resource(ClusterNodesView, '/clusters/<string:cluster_id>/nodes')
api.add_resource(ClusterNodeDetailView,
                 '/clusters/<string:cluster_id>/nodes/<string:node_name>')
api.add_resource(ClusterDeploymentsView,
                 '/clusters/<string:cluster_id>/deployments')
api.add_resource(ClusterDeploymentDetailView,
                 '/clusters/<string:cluster_id>/deployments/<string:namespace_name>/<string:deployment_name>')
api.add_resource(ClusterPvcsView, '/clusters/<string:cluster_id>/pvcs')
api.add_resource(ClusterPvcDetailView,
                 '/clusters/<string:cluster_id>/pvcs/<string:namespace_name>/<string:pvc_name>')
api.add_resource(ClusterPVsView, '/clusters/<string:cluster_id>/pvs')
api.add_resource(ClusterPVDetailView,
                 '/clusters/<string:cluster_id>/pvs/<string:pv_name>')
api.add_resource(ClusterPodsView, '/clusters/<string:cluster_id>/pods')
api.add_resource(ClusterPodDetailView,
                 '/clusters/<string:cluster_id>/pods/<string:namespace_name>/<string:pod_name>')
api.add_resource(ClusterServicesView, '/clusters/<string:cluster_id>/services')
api.add_resource(ClusterServiceDetailView,
                 '/clusters/<string:cluster_id>/services/<string:namespace_name>/<string:service_name>')
api.add_resource(ClusterJobsView, '/clusters/<string:cluster_id>/jobs')
api.add_resource(ClusterJobDetailView,
                 '/clusters/<string:cluster_id>/jobs/<string:namespace_name>/<string:job_name>')
api.add_resource(ClusterStorageClassView,
                 '/clusters/<string:cluster_id>/storage_classes')
api.add_resource(ClusterStorageClassDetailView,
                 '/clusters/<string:cluster_id>/storage_classes/<string:storage_class_name>')

# Roles routes
api.add_resource(RolesView, '/roles', endpoint='roles')
api.add_resource(RolesDetailView, '/roles/<string:role_id>', endpoint='roles_detail')

# User_Roles routes
api.add_resource(UserRolesView, '/user/<string:user_id>/roles',
                 endpoint='user_roles')

# Transaction routes
api.add_resource(TransactionRecordView, '/projects/<string:project_id>/transactions', endpoint='transactions')
api.add_resource(TransactionRecordDetailView, '/projects/<string:project_id>/transactions/<string:record_id>')

# Project route
api.add_resource(ProjectsView, '/projects', endpoint='projects')
api.add_resource(ProjectDetailView, '/projects/<string:project_id>')
api.add_resource(
    ProjectAppsView, '/projects/<string:project_id>/apps', endpoint='project_apps')
api.add_resource(ProjectCPUView, '/projects/<string:project_id>/metrics/cpu')
api.add_resource(ProjectMemoryUsageView,
                 '/projects/<string:project_id>/metrics/memory')
api.add_resource(ProjectNetworkRequestView,
                 '/projects/<string:project_id>/metrics/network')
api.add_resource(ProjectStorageUsageView,
                 '/projects/<string:project_id>/metrics/storage')

# User Project routes
api.add_resource(UserProjectsView, '/users/<string:user_id>/projects')

# App routes
api.add_resource(AppsView, '/apps')
api.add_resource(AppDetailView, '/apps/<string:app_id>')
api.add_resource(AppRevertView, '/apps/<string:app_id>/custom_domains')
api.add_resource(
    AppCpuUsageView, '/projects/<string:project_id>/apps/<string:app_id>/metrics/cpu')
api.add_resource(AppMemoryUsageView,
                 '/projects/<string:project_id>/apps/<string:app_id>/metrics/memory')
api.add_resource(AppNetworkUsageView,
                 '/projects/<string:project_id>/apps/<string:app_id>/metrics/network')
api.add_resource(
    AppLogsView, '/projects/<string:project_id>/apps/<string:app_id>/logs')
api.add_resource(AppStorageUsageView,
                 '/projects/<string:project_id>/apps/<string:app_id>/metrics/storage')
api.add_resource(AppDataSummaryView, '/apps/summary')

# Registry routes
api.add_resource(RegistriesView, '/registries')

# Databases
api.add_resource(ProjectDatabaseView,
                 '/projects/<string:project_id>/databases')
api.add_resource(ProjectDatabaseDetailView,
                 '/projects/<string:project_id>/databases/<string:database_id>')
api.add_resource(ProjectDatabaseAdminView, '/databases')
api.add_resource(ProjectDatabaseAdminDetailView,
                 '/databases/<string:database_id>')
api.add_resource(ProjectDatabaseResetView,
                 '/projects/<string:project_id>/databases/<string:database_id>/reset')
api.add_resource(ProjectDatabaseAdminResetView,
                 '/databases/<string:database_id>/reset')
api.add_resource(ProjectDatabasePasswordResetView,
                 '/projects/<string:project_id>/databases/<string:database_id>/reset_password')
api.add_resource(ProjectDatabaseAdminPasswordResetView,
                 '/databases/<string:database_id>/reset_password')
api.add_resource(ProjectDatabaseRetrievePasswordView,
                 '/projects/<string:project_id>/databases/<string:database_id>/password')
api.add_resource(ProjectDatabaseAdminRetrievePasswordView,
                 '/databases/<string:database_id>/password')
api.add_resource(DatabaseStatsView, '/databases/stats')
