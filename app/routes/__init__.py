from flask_restful import Api
from app.controllers import (
    IndexView, UsersView, UserLoginView, OrganisationsView,
    OrganisationDetailView, NamespacesView, OrganisationNamespaceView,
    NamespaceDetailView, DeploymentsView, RolesView,
    RolesDetailView, UserRolesView, ClustersView,
    OrgMemberView, OrgAdminView, ClusterDetailView, ClusterNamespacesView,
    ClusterNamespaceDetailView, ClusterNodesView, ClusterNodeDetailView,
    ClusterDeploymentsView, ClusterDeploymentDetailView, ClusterPvcsView, ClusterPvcDetailView,
    ClusterPVDetailView, ClusterPVsView, ClusterPodsView, ClusterPodDetailView,
    ClusterServiceDetailView, ClusterServicesView, ClusterJobsView, ClusterJobDetailView
)

api = Api()

# Index route
api.add_resource(IndexView, '/')

# User routes
api.add_resource(UsersView, '/users', endpoint='users')
api.add_resource(UserLoginView, '/users/login', endpoint='login')

# Organisation routes
api.add_resource(OrganisationsView, '/organisations', endpoint='organisations')
api.add_resource(OrganisationDetailView, '/organisations/<string:org_id>', endpoint='organisation')

# Organisation Members routes
api.add_resource(OrgMemberView, '/organisations/<string:organisation_id>/members', endpoint='org_members')

# Organisation Admins routes
api.add_resource(OrgAdminView, '/organisations/<string:organisation_id>/admins', endpoint='org_admins')

# Organisation Namespaces
api.add_resource(
    OrganisationNamespaceView, '/organisations/<string:organisation_id>/namespaces', endpoint='org_namespaces')

# Namespaces
api.add_resource(NamespacesView, '/namespaces', endpoint='namespaces')
api.add_resource(NamespaceDetailView, '/namespaces/<string:id>', endpoint='namespace')

# Deployments
api.add_resource(DeploymentsView, '/deployments', endpoint='deployments')

# Clusters
api.add_resource(ClustersView, '/clusters', endpoint='clusters')
api.add_resource(ClusterDetailView, '/clusters/<int:cluster_id>')
api.add_resource(ClusterNamespacesView, '/clusters/<int:cluster_id>/namespaces')
api.add_resource(ClusterNamespaceDetailView, '/clusters/<int:cluster_id>/namespaces/<string:namespace_name>')
api.add_resource(ClusterNodesView, '/clusters/<int:cluster_id>/nodes')
api.add_resource(ClusterNodeDetailView, '/clusters/<int:cluster_id>/nodes/<string:node_name>')
api.add_resource(ClusterDeploymentsView, '/clusters/<int:cluster_id>/deployments')
api.add_resource(ClusterDeploymentDetailView, '/clusters/<int:cluster_id>/deployments/<string:namespace_name>/<string:deployment_name>')
api.add_resource(ClusterPvcsView, '/clusters/<int:cluster_id>/pvcs')
api.add_resource(ClusterPvcDetailView, '/clusters/<int:cluster_id>/pvcs/<string:namespace_name>/<string:pvc_name>')
api.add_resource(ClusterPVsView, '/clusters/<int:cluster_id>/pvs')
api.add_resource(ClusterPVDetailView, '/clusters/<int:cluster_id>/pvs/<string:pv_name>')
api.add_resource(ClusterPodsView, '/clusters/<int:cluster_id>/pods')
api.add_resource(ClusterPodDetailView, '/clusters/<int:cluster_id>/pods/<string:namespace_name>/<string:pod_name>')
api.add_resource(ClusterServicesView, '/clusters/<int:cluster_id>/services')
api.add_resource(ClusterServiceDetailView, '/clusters/<int:cluster_id>/services/<string:namespace_name>/<string:service_name>')
api.add_resource(ClusterJobsView, '/clusters/<int:cluster_id>/jobs')
api.add_resource(ClusterJobDetailView, '/clusters/<int:cluster_id>/jobs/<string:namespace_name>/<string:job_name>')


# Roles routes
api.add_resource(RolesView, '/roles', endpoint='roles')

# User_Roles routes
api.add_resource(UserRolesView, '/user/<string:user_id>/roles', endpoint='user_roles')
