# import all controllers

from .index import IndexView
from .users import (
    UsersView, UserLoginView, UserEmailVerificationView,
    EmailVerificationRequest, ForgotPasswordView, ResetPasswordView,
    UserDetailView, AdminLoginView)
from .organisation import OrganisationsView, OrganisationDetailView
from .namespaces import NamespacesView, OrganisationNamespaceView, NamespaceDetailView
from .deployments import DeploymentsView
from .clusters import (
    ClustersView, ClusterDetailView, ClusterNamespacesView,
    ClusterNamespaceDetailView, ClusterNodesView, ClusterNodeDetailView,
    ClusterDeploymentsView, ClusterDeploymentDetailView, ClusterPvcsView,
    ClusterPvcDetailView, ClusterPVsView, ClusterPVDetailView,
    ClusterPodsView, ClusterPodDetailView, ClusterServicesView,
    ClusterServiceDetailView, ClusterJobsView, ClusterJobDetailView,
    ClusterStorageClassView, ClusterStorageClassDetailView)
from .roles import RolesView, RolesDetailView
from .user_role import UserRolesView
from .organisation_admins import OrgAdminView
from .organisation_members import OrgMemberView
from .project import (
    ProjectsView, ProjectDetailView, UserProjectsView,
    ProjectCPUView, ProjectMemoryUsageView, ProjectNetworkRequestView, ProjectStorageUsageView)
from .app import (AppsView, ProjectAppsView, AppDetailView, AppLogsView,
                  AppCpuUsageView, AppMemoryUsageView, AppNetworkUsageView, AppStorageUsageView)
from .registry import RegistriesView
from .project_database import (ProjectDatabaseView, ProjectDatabaseDetailView, ProjectDatabaseAdminView,
                               ProjectDatabaseAdminDetailView, ProjectDatabaseResetView, ProjectDatabaseAdminResetView,
                            ProjectDatabasePasswordResetView, ProjectDatabaseAdminPasswordResetView,
                            ProjectDatabaseRetrievePasswordView,ProjectDatabaseAdminRetrievePasswordView)
