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

        projects_page=request.args.get('projects_page',1)
        users_page=request.args.get('users_page',1)
        tags_page=request.args.get('tags_page',1)

        if not keywords:
            return dict(
                projects=[],
                users=[],
                tags = []
            ),200
        
        def create_pagination(pagination):
            return {
                'total': pagination.total,
                'pages': pagination.pages,
                'page': pagination.page,
                'per_page': pagination.per_page,
                'next': pagination.next_num,
                'prev': pagination.prev_num
            }

        #Schemas
        projectSchema = ProjectListSchema(many=True)
        userSchema = UserSchema(many=True)
        tagSchema = TagListSchema(many=True)
        
        # projects 
        projects_pagination = Project.query.filter(Project.name.ilike('%'+keywords+'%')).order_by(Project.date_created.desc()).paginate(
                            page=int(projects_page), per_page=10, error_out=False)

        #Tags
        tags_pagination = Tag.query.filter(Tag.name.ilike('%'+keywords+'%')).order_by(Tag.date_created.desc()).paginate(
                            page=int(tags_page), per_page=10, error_out=False)

        #users 
        search_filter = or_(
            User.name.ilike(f'%{keywords}%'),
            User.email.ilike(f'%{keywords}%')
        )
        users_pagination = User.query.filter(search_filter).order_by(User.date_created.desc()).paginate(
                            page=int(users_page), per_page=10, error_out=False)

        project_data , _ = projectSchema.dumps(projects_pagination.items)
        users_data , _ = userSchema.dumps(users_pagination.items)
        tags_data , _ = tagSchema.dumps(tags_pagination.items)

        return dict(
            projects={
                'pagination':create_pagination(projects_pagination),
                'items':json.loads(project_data)
            },
            users={
                'pagination':create_pagination(users_pagination),
                'items' : json.loads(users_data)
            },
            tags = {
                'pagination':create_pagination(tags_pagination),
                'items':json.loads(tags_data)
            }
        ) , 200