
import json
from app.schemas.project_users import UserIndexSchema
from app.schemas.tags import TagSchema, TagsDetailSchema
from flask_restful import Resource, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.tags import Tag, TagFollowers
from app.helpers.decorators import admin_required


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
        tag_schema = TagsDetailSchema()

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

    @ jwt_required
    def get(self, tag_id):
        tag = Tag.get_by_id(tag_id)
        follower_schema = UserIndexSchema(many=True)

        followers = tag.followers
        users_data, errors = follower_schema.dumps(followers)

        if errors:
            return dict(status='fail', message=errors), 400

        return dict(
            status='success',
            data=dict(followers=json.loads(users_data))
        ), 200

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
