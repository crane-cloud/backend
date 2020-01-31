from flask_restful import Api
from app.controllers import (
    IndexView, UsersView, UserLoginView, OrganisationsView,
    OrganisationDetailView, NamespacesView, OrganisationNamespaceView,
    NamespaceDetailView, DeploymentsView, RolesView, UserRolesView, ClustersView,
    OrgMemberView, OrgAdminView,
    OrgAdminDetailView, ClusterDetailView
)

api = Api()

# Index route
api.add_resource(IndexView, '/')

# User routes
api.add_resource(UsersView, '/users', endpoint='users')
api.add_resource(UserLoginView, '/users/login', endpoint='login')

# Organisation routes
api.add_resource(OrganisationsView, '/organisations', endpoint='organisations')
api.add_resource(OrganisationDetailView, '/organisations/<int:org_id>', endpoint='organisation')

# Organisation Members routes
api.add_resource(OrgMemberView, '/organisations/<int:organisation_id>/members', endpoint='org_members')

# Organisation Admins routes
api.add_resource(OrgAdminView, '/organisations/admins', endpoint='org_admins')
api.add_resource(OrgAdminDetailView, '/organisation/admin/<int:organisation_id>', endpoint='org_admin')

# Organisation Namespaces
api.add_resource(
    OrganisationNamespaceView, '/organisations/<int:organisation_id>/namespaces', endpoint='org_namespaces')

# Namespaces
api.add_resource(NamespacesView, '/namespaces', endpoint='namespaces')
api.add_resource(NamespaceDetailView, '/namespaces/<int:id>', endpoint='namespace')

# Deployments
api.add_resource(DeploymentsView, '/deployments', endpoint='deployments')

# Clusters
api.add_resource(ClustersView, '/clusters', endpoint='clusters')
api.add_resource(ClusterDetailView, '/clusters/<int:cluster_id>')


# Roles routes
api.add_resource(RolesView, '/roles', endpoint='roles')


# User_Roles routes
api.add_resource(UserRolesView, '/user/<int:user_id>/roles', endpoint='user_roles')
