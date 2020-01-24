# import all controllers

from .index import IndexView
from .users import UsersView, UserLoginView
from .organisation import OrganisationsView, OrganisationDetailView
from .namespaces import NamespacesView, OrganisationNamespaceView, NamespaceDetailView
from .deployments import DeploymentsView
from .clusters import ClustersView
from .roles import RolesView
from .user_role import UserRolesView, UserRolesDetailView
from .organisation_members import OrgMemberView, OrgMemberDetailView