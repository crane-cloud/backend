from flask_restful import Api
from app.controllers import (
    IndexView, UsersView, UserLoginView, OrganisationsView,
    OrganisationDetailView, NamespacesView, OrganisationNamespaceView,
    NamespaceDetailView, DeploymentsView, RolesView, UserRolesView, ClustersView,
    OrgMemberView, OrgMemberDetailView, OrgAdminView, ClusterDetailView
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
api.add_resource(OrgMemberView, '/organisations/members', endpoint='org_members')
api.add_resource(OrgMemberDetailView, '/organisation/member/<int:organisation_id>', endpoint='org_member')

# Organisation Admins routes
api.add_resource(OrgAdminView, '/organisations/<int:organisation_id>/admins', endpoint='org_admins')

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
api.add_resource(RolesDetailView, '/roles/<int:role_id>', endpoint='role')


# User_Roles routes
api.add_resource(UserRolesView, '/user/<int:user_id>/roles', endpoint='user_roles')
