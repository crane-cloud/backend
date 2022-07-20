# import all controllers

from .index import IndexView
from .users import (
    UsersView, UserLoginView, UserEmailVerificationView,
    EmailVerificationRequest, ForgotPasswordView, ResetPasswordView,
    UserDetailView, AdminLoginView, OAuthView, UserDataSummaryView, UserAdminUpdateView)
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
from .credit_assignments import CreditAssignmentView
from .credits import CreditView
from .user_role import UserRolesView
from .transactions import TransactionRecordView, TransactionRecordDetailView
from .project import (
    ProjectsView, ProjectDetailView, UserProjectsView, ProjectGetCostsView,
    ProjectCPUView, ProjectMemoryUsageView, ProjectNetworkRequestView, ProjectStorageUsageView)
from .app import (AppsView, ProjectAppsView, AppDetailView, AppLogsView,
                  AppCpuUsageView, AppMemoryUsageView, AppNetworkUsageView, AppStorageUsageView,
                  AppDataSummaryView, AppRevertView)
from .registry import RegistriesView
from .project_database import (ProjectDatabaseView, ProjectDatabaseDetailView, ProjectDatabaseAdminView,
                               ProjectDatabaseAdminDetailView, ProjectDatabaseResetView, ProjectDatabaseAdminResetView,
                               ProjectDatabasePasswordResetView, ProjectDatabaseAdminPasswordResetView,
                               ProjectDatabaseRetrievePasswordView, ProjectDatabaseAdminRetrievePasswordView, DatabaseStatsView)
from .billing_invoice import (BillingInvoiceView)
from .system_status import SystemStatusView
