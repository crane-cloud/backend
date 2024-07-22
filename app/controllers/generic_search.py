from app.models.project import Project
from app.models.user import User
from app.models.tags import Tag
from app.schemas.tags import TagListSchema
from app.schemas.user import UserSchema
from app.schemas.project import ProjectListSchema
from flask import current_app
from flask_restful import Resource, request
from app.models.project import Project
from flask_jwt_extended import jwt_required
import json
from sqlalchemy import or_



class GenericSearchView(Resource):
    @jwt_required
    def get(self):
        keywords = request.args.get('keywords', '')

        if not keywords:
            return dict(
                projects=[],
                users=[],
                tags = []
            ),200

        #Schemas
        projectSchema = ProjectListSchema(many=True)
        userSchema = UserSchema(many=True)
        tagSchema = TagListSchema(many=True)
        
        # projects 
        projects = Project.query.filter(Project.name.ilike('%'+keywords+'%')).order_by(Project.date_created.desc())

        #Tags
        tags = Tag.query.filter(Tag.name.ilike('%'+keywords+'%')).order_by(Tag.date_created.desc())

        #users 
        search_filter = or_(
            User.name.ilike(f'%{keywords}%'),
            User.email.ilike(f'%{keywords}%')
        )
        users = User.query.filter(search_filter).order_by(User.date_created.desc())

        project_data , _ = projectSchema.dumps(projects)
        users_data , _ = userSchema.dumps(users)
        tags_data , _ = tagSchema.dumps(tags)

        return dict(
            projects=json.loads(project_data),
            users=json.loads(users_data),
            tags = json.loads(tags_data)
        ) , 200