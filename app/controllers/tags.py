
from flask_restful import Resource, request
from flask_jwt_extended import jwt_required
from app.schemas.tags import TagSchema
from app.models.tags import Tag
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
        tag_id_schema = TagSchema()

        tag = Tag.get_by_id(tag_id)

        tags_data = tag_id_schema.dump(tag)

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
