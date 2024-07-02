
from flask_restful import Resource, request
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt_claims
from app.schemas.project_tags import ProjectTagSchema
from app.models.project_tag import ProjectTag
from app.helpers.decorators import admin_required




class ProjectTagsView(Resource):

    @jwt_required
    def post(self):
        tags_data = request.get_json()

        project_tag_schema = ProjectTagSchema()
                
        for _tag in tags_data:
            validated_tag_data , errors = project_tag_schema.load({'name' : _tag})
            if not ProjectTag.find_first(name=validated_tag_data['name']):
                tag = ProjectTag(**validated_tag_data)
                tag.save()
            
        return dict(
            status='success',
            message='Tags saved successfully'
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

        project_tag = ProjectTag.get_by_id(tag_id)

        tags_data = project_tag_id_schema.dump(project_tag)

        return dict(
            status="success",
            data=tags_data.data
        ) , 200
    
    @admin_required
    def delete(self, tag_id):

        current_user_roles = get_jwt_claims()['roles']

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





        



