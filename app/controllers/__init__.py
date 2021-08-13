# import all controllers

from .index import IndexView
from .users import (
    UsersView, UserLoginView, UserEmailVerificationView,
    EmailVerificationRequest, ForgotPasswordView, ResetPasswordView,
    UserDetailView, AdminLoginView)
from .namespaces import NamespacesView, NamespaceDetailView
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
from .project import (
    ProjectsView, ProjectDetailView, UserProjectsView,
    ProjectCPUView, ProjectMemoryUsageView, ProjectNetworkRequestView, ProjectStorageUsageView)
from .app import (AppsView, ProjectAppsView, ProjectAppsDetailView, AppDetailView, AppLogsView,
                  AppCpuUsageView, AppMemoryUsageView, AppNetworkUsageView, AppStorageUsageView)
from .registry import RegistriesView
from .project_database import (ProjectDatabaseView, ProjectDatabaseDetailView, ProjectDatabaseAdminView,
                               ProjectDatabaseAdminDetailView, ProjectDatabaseResetView, ProjectDatabaseAdminResetView,
                            ProjectDatabasePasswordResetView, ProjectDatabaseAdminPasswordResetView,
                            ProjectDatabaseRetrievePasswordView,ProjectDatabaseAdminRetrievePasswordView)
