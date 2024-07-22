from app.models.project import Project
from app.schemas.project import ProjectListSchema
from flask import current_app
from flask_restful import Resource, request
from app.models.project import Project
from flask_jwt_extended import jwt_required
import json


class GenericSearchView(Resource):
    @jwt_required
    def get(self):
        keywords = request.args.get('keywords', '')

        #Schemas
        projectSchema = ProjectListSchema(many=True)
        
        # projects 
        projects = Project.query.filter(Project.name.ilike('%'+keywords+'%')).order_by(Project.date_created.desc())

        project_data , errors = projectSchema.dumps(projects)

        return dict(projects=json.loads(project_data)) , 200