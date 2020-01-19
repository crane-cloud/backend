from flask_restful import Api
from app.controllers import (
    IndexView, UsersView, UserLoginView, OrganisationsView,
    OrganisationDetailView, NamespacesView, OrganisationNamespaceView,
    NamespaceDetailView, DeploymentsView
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

# Organisation Namespaces
api.add_resource(
    OrganisationNamespaceView, '/organisations/<int:organisation_id>/namespaces', endpoint='org_namespaces')

# Namespaces
api.add_resource(NamespacesView, '/namespaces', endpoint='namespaces')
api.add_resource(NamespaceDetailView, '/namespaces/<int:id>', endpoint='namespace')

# Deployments
api.add_resource(DeploymentsView, '/deployments', endpoint='deployments')
