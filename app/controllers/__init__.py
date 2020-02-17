# import all controllers

from .index import IndexView
from .users import UsersView, UserLoginView
from .organisation import OrganisationsView, OrganisationDetailView
from .namespaces import NamespacesView, OrganisationNamespaceView, NamespaceDetailView
from .deployments import DeploymentsView
from .clusters import (
    ClustersView, ClusterDetailView, ClusterNamespacesView,
    ClusterNamespaceDetailView, ClusterNodesView, ClusterNodeDetailView,
    ClusterDeploymentsView, ClusterDeploymentDetailView, ClusterPvcsView,
    ClusterPvcDetailView, ClusterPVsView, ClusterPVDetailView,
    ClusterPodsView, ClusterPodDetailView,ClusterServicesView,
    ClusterServiceDetailView, ClusterJobsView, ClusterJobDetailView)
from .roles import RolesView, RolesDetailView
from .user_role import UserRolesView
from .organisation_admins import OrgAdminView
from .organisation_members import OrgMemberView
from .project import ProjectsView, ProjectDetailView, UserProjectsView
