# import all controllers

from .index import IndexView
from .users import UsersView, UserLoginView
from .organisation import OrganisationsView, OrganisationDetailView
from .namespaces import NamespacesView, OrganisationNamespaceView, NamespaceDetailView
from .deployments import DeploymentsView
from .clusters import ClustersView, ClusterDetailView
from .roles import RolesView
from .user_role import UserRolesView
from .organisation_members import OrgMemberView
from .organisation_admins import OrgAdminView, OrgAdminDetailView