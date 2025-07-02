from flask_restful import Resource, request
from app.models.user import User
from app.helpers.activity_logger import filter_logs , get_logs
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.helpers.decorators import admin_required
from app.models.app import App
from app.models.project import Project
from app.models.app_state import AppState
import datetime
from app.schemas.app import AppSchema
from app.models.project_users import ProjectUser
from app.schemas.project import ProjectListSchema
from app.helpers.pagination import paginate


class AdminReportingView(Resource):

    @admin_required
    def get(self):
        # this endpoint should return apps and projects 
        # Default time back is a month
        thirty_days_ago = (datetime.datetime.now() - datetime.timedelta(days=30)).strftime('%Y-%m-%d')
        filter_data = {
            'start': request.args.get('start', thirty_days_ago),
            'end': request.args.get('end', datetime.datetime.now().strftime('%Y-%m-%d')),
            'disabled': request.args.get('disabled', 'false'),# 'true' or 'false'
            'page': request.args.get('page', 0),
            'per_page': request.args.get('per_page', 10),
            'search': request.args.get('search', ''),
            'deleted': request.args.get('deleted', 'false'),# 'true' or 'false'
            'cluster_id': request.args.get('cluster_id'),
            'status': request.args.get('status', None),
            'is_modal': request.args.get('is_modal', None),  # 'true' or 'false'
            'is_ai': request.args.get('is_ai', None),  # 'true' or 'false'
            'is_notebook': request.args.get('is_notebook', None),  # 'true' or 'false'
            'type': request.args.get('type', None)  # 'apps' or 'projects'  
        }

        if filter_data['type'] and filter_data['type'] not in ['apps', 'projects']:
            return dict(message="Invalid type provided, should be 'apps' or 'projects'"), 400
    
        if filter_data['status'] and filter_data['status'] not in ['running', 'down', None]:
            return dict(message="Invalid status provided, should be 'running', 'down' or None"), 400

        if filter_data['disabled'] and filter_data['disabled'] not in ['true', 'false', None]:
            return dict(message="Invalid disabled provided, should be 'true', 'false' or None"), 400
      
        report_data = {}

        if filter_data['type'] == 'apps' or not filter_data['type']:
            app_query = App.query

            if filter_data['deleted'] == 'true':
                app_query = app_query.filter_by(deleted=True)
            else:
                app_query = app_query.filter_by(deleted=False)

            if filter_data['search']:
                app_query = app_query.filter(App.name.ilike(f"%{filter_data['search']}%"))            

            if filter_data['is_modal'] == 'true':
                app_query = app_query.filter_by(is_modal=True)

            if filter_data['is_modal'] == 'false':
                app_query = app_query.filter(
                    (App.is_modal == False) | (App.is_modal.is_(None))
                )

            if filter_data['is_ai'] == 'true':
                app_query = app_query.filter_by(is_ai=True)

            if filter_data['is_ai'] == 'false':
                app_query = app_query.filter(
                    (App.is_ai == False) | (App.is_ai.is_(None))
                )

            if filter_data['is_notebook'] == 'true':
                app_query = app_query.filter_by(is_notebook=True)
            
            if filter_data['is_notebook'] == 'false':
                app_query = app_query.filter(
                    (App.is_notebook == False) | (App.is_notebook.is_(None))
                )
            if filter_data['disabled'] == 'true':
                app_query = app_query.filter_by(disabled=True)
                app_query = app_query.filter_by(admin_disabled=True)

            if filter_data['disabled'] == 'false':
                app_query = app_query.filter_by(disabled=False)
                app_query = app_query.filter_by(admin_disabled=False)

            if filter_data['start']:
                start_date = datetime.datetime.strptime(filter_data['start'], '%Y-%m-%d')
                app_query = app_query.filter(App.date_created >= start_date)

            if filter_data['end']:
                end_date = datetime.datetime.strptime(filter_data['end'], '%Y-%m-%d')
                app_query = app_query.filter(App.date_created <= end_date)

            if filter_data['cluster_id']:
                # Filter apps by cluster_id via the related project
                app_query = app_query.join(Project, App.project_id == Project.id).filter(Project.cluster_id == filter_data['cluster_id'])

            if filter_data['status'] == 'running':
                app_query = app_query.join(AppState).filter(AppState.status == 'running')

            if filter_data['status'] == 'down':
                # Show apps with any status except 'running'
                app_query = app_query.join(AppState).filter(AppState.status != 'running')


    
            paginated_apps = app_query.order_by(App.date_created.desc()).paginate(
                    page=filter_data['page'], per_page=filter_data['per_page'], error_out=False)
            
            report_data['apps'] = paginated_apps.items
            report_data['app_pagination'] =  {
                    'total': paginated_apps.total,
                    'pages': paginated_apps.pages,
                    'page': paginated_apps.page,
                    'per_page': paginated_apps.per_page,
                    'next': paginated_apps.next_num,
                    'prev': paginated_apps.prev_num
                }

        if filter_data['type'] == 'projects' or not filter_data['type']:
            project_query = Project.query
            if filter_data['deleted'] == 'true':
                project_query = project_query.filter(Project.deleted.is_(True))
            else:
                project_query = project_query.filter(Project.deleted.is_(False))

            if filter_data['search']:
                project_query = project_query.filter(Project.name.ilike(f"%{filter_data['search']}%"))


            if filter_data['cluster_id']:
                project_query = project_query.filter(Project.cluster_id == filter_data['cluster_id'])

            if filter_data['disabled'] == 'true':
                project_query = project_query.filter_by(disabled=True)
                project_query = project_query.filter_by(admin_disabled=True)

            if filter_data['disabled'] == 'false':
                project_query = project_query.filter_by(disabled=False)
                project_query = project_query.filter_by(admin_disabled=False)
            

            if filter_data['start']:
                start_date = datetime.datetime.strptime(filter_data['start'], '%Y-%m-%d')
                project_query = project_query.filter(Project.date_created >= start_date)
            
            if filter_data['end']:
                end_date = datetime.datetime.strptime(filter_data['end'], '%Y-%m-%d')
                project_query = project_query.filter(Project.date_created <= end_date)
                

            paginated_projects = project_query.order_by(Project.date_created.desc()).paginate(
                    page=filter_data['page'], per_page=filter_data['per_page'], error_out=False)
            

            report_data['projects'] = paginated_projects.items
            report_data['project_pagination'] = {
                    'total': paginated_projects.total,
                    'pages': paginated_projects.pages,
                    'page': paginated_projects.page,
                    'per_page': paginated_projects.per_page,
                    'next': paginated_projects.next_num,
                    'prev': paginated_projects.prev_num
                }

        projectSchema = ProjectListSchema(many=True)
        appSchema = AppSchema(many=True)
        projects = projectSchema.dump(report_data.get('projects', []))
        apps = appSchema.dump(report_data.get('apps', []))

        return {
                "projects": projects,
                "apps": apps,
                "pagination": {
                    "page": filter_data['page'],
                    "per_page": filter_data['per_page'],
                    "total_projects": report_data.get('project_pagination', {}).get('total', 0),
                    "total_apps": report_data.get('app_pagination', {}).get('total', 0),
                    "total_pages_projects": report_data.get('project_pagination', {}).get('pages', 0),
                    "total_pages_apps": report_data.get('app_pagination', {}).get('pages', 0),
                }

        }