
from flask_restful import Resource, request
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt_claims
from app.schemas.project_tags import ProjectTagSchema
from app.models.project_tag import ProjectTag
import json
import uuid
from app.helpers.admin import is_admin



class ProjectTagsView(Resource):

    @jwt_required
    def post(self):
        tags_data = request.get_json()

        project_tag_schema = ProjectTagSchema()
        
        saved_tags = []
        already_existing = []
        
        for _tag in tags_data:
            validated_tag_data , errors = project_tag_schema.load({'name' : _tag})
            if not ProjectTag.find_first(name=validated_tag_data['name']):
                tag = ProjectTag(**validated_tag_data)
                tag.save()
                saved_tags.append(tag)
            else :
                already_existing.append(_tag)

        new_tags_data , errs = ProjectTagSchema(many=True).dump(saved_tags)

        return dict(
            status='success',
            data=new_tags_data,
            Isexisting=already_existing
        ) , 201
    
    def get(self):
        keywords = request.args.get('keywords', None)

        project_tag_schema = ProjectTagSchema(many=True)

        project_tags = ProjectTag.find_all()

        if keywords :
            project_tags = ProjectTag.query.filter(ProjectTag.name.ilike(f'%{keywords}%'))

        tags_data = project_tag_schema.dump(project_tags)

        return dict(
            status="success",
            data=tags_data.data
        ) , 200

class ProjectTagsDetailView(Resource):
    def get(self, tag_id):

        project_tag_id_schema = ProjectTagSchema()

        project_tag = ProjectTag.get_by_id(uuid.UUID(tag_id))

        tags_data = project_tag_id_schema.dump(project_tag)

        return dict(
            status="success",
            data=tags_data.data
        ) , 200
    
    @jwt_required
    def delete(self, tag_id):

        current_user_roles = get_jwt_claims()['roles']

        if not is_admin(current_user_roles):
            return dict(
                status='fail',
                message='Only admins are allowed to delete tags'
            ) , 401

        tag = ProjectTag.get_by_id(tag_id)

        deleted = tag.soft_delete()

        if not deleted:
            return dict(
                status='fail',
                message='An error occured during deletion'
            ) , 500
        
        return dict(
            status='success',
            message=f"Tag {tag_id} successfully deleted"
        ) , 200





        



