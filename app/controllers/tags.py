
import json
from app.models.project import Project
from app.models.user import User
from app.schemas.project import ProjectSchema
from app.schemas.project_users import UserIndexSchema
from app.schemas.tags import TagSchema, TagsDetailSchema
from app.schemas.user import UserSchema
from flask_restful import Resource, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.tags import ProjectTag, Tag, TagFollowers
from app.helpers.decorators import admin_required
from app.models import db


class TagsView(Resource):

    @jwt_required
    def post(self):
        tags_data = request.get_json()
        tag_schema = TagSchema()
        none_existing_tags = []

        for tag in tags_data:
            validated_tag_data, errors = tag_schema.load({'name': tag})
            if errors:
                return dict(status="fail", message=errors), 400
            if not Tag.find_first(name=validated_tag_data['name']):
                none_existing_tags.append(Tag(**validated_tag_data))

        if none_existing_tags:
            if Tag.bulk_save(none_existing_tags):
                return dict(
                    status='success',
                    message='Tags saved successfully'
                ), 201
            else:
                return dict(
                    status='fail',
                    message='An error occurred while saving tags'
                ), 500
        else:
            return dict(
                status='success',
                message='No new tags to save'
            ), 201

    @jwt_required
    def get(self):
        keywords = request.args.get('keywords', None)

        tag_schema = TagSchema(many=True)

        tags = Tag.find_all()
        print(tags)
        if keywords:
            tags = Tag.query.filter(
                Tag.name.ilike(f'%{keywords}%'))

        tags_data = tag_schema.dump(tags)

        return dict(
            status="success",
            data=tags_data.data
        ), 200


class TagsDetailView(Resource):

    @jwt_required
    def get(self, tag_id):
        tag_schema = TagSchema()

        tag = Tag.get_by_id(tag_id)

        tags_data = tag_schema.dump(tag)

        return dict(
            status="success",
            data=tags_data.data
        ), 200

    @admin_required
    def delete(self, tag_id):

        tag = Tag.get_by_id(tag_id)

        deleted = tag.soft_delete()

        if not deleted:
            return dict(
                status='fail',
                message='An error occured during deletion'
            ), 500

        return dict(
            status='success',
            message=f"Tag {tag_id} successfully deleted"
        ), 200


class TagFollowingView(Resource):
    @ jwt_required
    def post(self, tag_id):
        current_user_id = get_jwt_identity()
        tag = Tag.get_by_id(tag_id)

        if not tag:
            return dict(status='fail', message=f'Tag with id {tag_id} not found'), 404


        existing_tag_follow = TagFollowers.find_first(
            user_id=current_user_id, tag_id=tag_id)
        if existing_tag_follow:
            return dict(status='fail', message=f'You are already following tag with id {tag_id}'), 409

        new_tag_follow = TagFollowers(
            user_id=current_user_id, tag_id=tag_id)

        saved_tag_follow = new_tag_follow.save()

        if not saved_tag_follow:
            return dict(status='fail', message='Internal Server Error'), 500

        return dict(
            status='success',
            message=f'You are now following tag with id {tag_id}'
        ), 201

    @jwt_required
    def get(self, tag_id):
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        if per_page > 100:
            per_page = 100
        
        if page < 1:
            page = 1
        
        tag = Tag.get_by_id(tag_id)
        
        if not tag:
            return dict(status='fail', message=f'Tag with id {tag_id} not found'), 404
        
        try:
            query = db.session.query(User).join(
                    TagFollowers, User.id == TagFollowers.user_id
                ).filter(
                    TagFollowers.tag_id == tag_id
                ).order_by(TagFollowers.date_created.desc())
                            
            total_followers_count = query.count()
    
            paginated_result = query.paginate(
                page=page,
                per_page=per_page,
                error_out=False
            )
            
            follower_schema = UserSchema(many=True)
            schema_result = follower_schema.dump(paginated_result.items)

            if hasattr(schema_result, 'data'):
                followers_data = schema_result.data
            else:
                followers_data = schema_result
          
            if followers_data is None:
                followers_data = []
            elif not isinstance(followers_data, list):
                try:
                    followers_data = list(followers_data)
                except:
                    followers_data = []
            
            pagination = {
                'total': paginated_result.total,
                'pages': paginated_result.pages,
                'page': paginated_result.page,
                'per_page': paginated_result.per_page,
                'next': paginated_result.next_num,
                'prev': paginated_result.prev_num,
                'has_next': paginated_result.has_next,
                'has_prev': paginated_result.has_prev
            }
            
            tag_info = dict(
                id=str(tag.id),
                name=tag.name,
                followers_count=total_followers_count
            )
            
            return dict(
                status='success',
                data=dict(
                    tag=tag_info,
                    followers=followers_data,
                    pagination=pagination
                )
            ), 200
            
        except Exception as e:
            return dict(status='fail', message='Internal Server Error'), 500
        
    @ jwt_required
    def delete(self, tag_id):
        current_user_id = get_jwt_identity()
        tag = Tag.get_by_id(tag_id)

        if not tag:
            return dict(status='fail', message=f'Tag with id {tag_id} not found'), 404

        existing_tag_follow = TagFollowers.find_first(
            user_id=current_user_id, tag_id=tag_id)
        if not existing_tag_follow:
            return dict(status='fail', message=f'You are not following tag with id {tag_id}'), 409

        deleted_tag = existing_tag_follow.delete()

        if not deleted_tag:
            return dict(status='fail', message='Internal Server Error'), 500

        return dict(
            status='success',
            message=f'You are nolonger following tag with id {tag_id}'
        ), 201




class TagProjectsView(Resource):
    @jwt_required
    def get(self, tag_id):
       
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)

        if per_page > 100:
            per_page = 100

        if page < 1:
            page = 1

        tag = Tag.get_by_id(tag_id)
        tag_schema = TagSchema()
        tag_data = tag_schema.dump(tag)
            
        
        if not tag:
            return dict(status='fail', message=f'Tag with id {tag_id} not found'), 404

        try:
            query = db.session.query(Project).join(
                ProjectTag, Project.id == ProjectTag.project_id
            ).filter(
                ProjectTag.tag_id == tag_id,
                Project.deleted.is_(False)
            ).order_by(Project.date_created.desc())
            total_projects_count = query.count()
            
            paginated_result = query.paginate(
                page=page, 
                per_page=per_page, 
                error_out=False
            )

            project_schema = ProjectSchema(many=True)
            schema_result = project_schema.dump(paginated_result.items)

            if hasattr(schema_result, 'data'):
                projects_data = schema_result.data
            else:
                projects_data = schema_result
                
            if projects_data is None:
                projects_data = []
            elif not isinstance(projects_data, list):
                try:
                    projects_data = list(projects_data)
                except:
                    projects_data = []
            
            pagination = {
                'total': paginated_result.total,
                'pages': paginated_result.pages,
                'page': paginated_result.page,
                'per_page': paginated_result.per_page,
                'next': paginated_result.next_num,
                'prev': paginated_result.prev_num,
                'has_next': paginated_result.has_next,
                'has_prev': paginated_result.has_prev
            }
                
            tag_info = dict(
                id=str(tag.id),
                name=tag.name,
                projects_count=total_projects_count
            )
            return dict(
                status='success',
                data=dict(
                    tag=tag_info,
                    projects=projects_data,
                    pagination=pagination
                    )
                ), 200
                
        except Exception as e:      
            return dict(status='fail', message='Internal Server Error'), 500