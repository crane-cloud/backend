from flask import request
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import or_, desc, func

from app.models.user import User, Followers
from app.models.project import Project
from app.models.tags import ProjectTag, Tag, TagFollowers
from app.models.project_users import ProjectFollowers
from app.schemas.user import UserSchema
from app.schemas.project import ProjectSchema
from app.schemas.tags import TagSchema


class SocialService:
    """Service class for handling social data operations"""
    
    @staticmethod
    def _handle_schema_result(schema_result):
        """Helper method to handle different schema dump return formats"""
        if hasattr(schema_result, 'data'):
            data = schema_result.data
        else:
            data = schema_result

        if data is None:
            data = []
        elif not isinstance(data, list):
            try:
                data = list(data)
            except:
                data = []
        
        return data
    
    @staticmethod
    def get_projects_data(current_user, search=None, filter_type=None, page=1, per_page=10, paginate=True):
        """Get projects data using schema methods for counts"""
        
        # Base query
        query = Project.query.filter(
            Project.deleted == False,
            Project.disabled == False,
            Project.admin_disabled == False,
            Project.is_public == True
        )
        
        if search and search.strip():
            search_filter = or_(
                Project.name.ilike(f'%{search}%'),
                Project.description.ilike(f'%{search}%'),
                Project.alias.ilike(f'%{search}%')
            )
            query = query.filter(search_filter)

        if filter_type == 'trending':
            query = query.outerjoin(ProjectFollowers).group_by(Project.id).order_by(
                desc(func.count(ProjectFollowers.id))
            )
        elif filter_type == 'recently_updated':
            query = query.order_by(desc(Project.updated_at))
        elif filter_type == 'newly_added':
            query = query.order_by(desc(Project.date_created))
        else:
            query = query.order_by(desc(Project.date_created))
        
        if paginate:
            paginated = query.paginate(page=page, per_page=per_page, error_out=False)
            projects = paginated.items
    
            project_schema = ProjectSchema(many=True)
            schema_result = project_schema.dump(projects)
            projects_data = SocialService._handle_schema_result(schema_result)
            
            return {
                'projects': projects_data,
                'pagination': {
                    'total': paginated.total,
                    'pages': paginated.pages,
                    'page': paginated.page,
                    'per_page': paginated.per_page,
                    'next': paginated.next_num,
                    'prev': paginated.prev_num
                }
            }
        else:
            offset = (page - 1) * per_page
            projects = query.offset(offset).limit(per_page).all()
    
            project_schema = ProjectSchema(many=True)
            schema_result = project_schema.dump(projects)
            projects_data = SocialService._handle_schema_result(schema_result)
            
            return projects_data

    @staticmethod
    def get_users_data(current_user, search=None, filter_type=None, page=1, per_page=10, paginate=True):
        """Get users data using schema methods for counts"""
        
        query = User.query.filter(
            User.disabled == False,
            User.admin_disabled == False,
            User.is_public == True,
            User.verified == True
        )
        
        if search and search.strip():
            search_filter = or_(
                User.name.ilike(f'%{search}%'),
                User.username.ilike(f'%{search}%'),
                User.biography.ilike(f'%{search}%')
            )
            query = query.filter(search_filter)

        if filter_type == 'trending':
            query = query.outerjoin(Followers, Followers.followed_id == User.id).group_by(User.id).order_by(
                desc(func.count(Followers.follower_id))
            )
        elif filter_type == 'recently_updated':
            query = query.order_by(desc(User.last_seen))
        elif filter_type == 'newly_added':
            query = query.order_by(desc(User.date_created))
        else:
            query = query.order_by(desc(User.date_created))
        
        if paginate:
            paginated = query.paginate(page=page, per_page=per_page, error_out=False)
            users = paginated.items

            user_schema = UserSchema(many=True)
            schema_result = user_schema.dump(users)
            users_data = SocialService._handle_schema_result(schema_result)
            if current_user:
                for user_data, user_obj in zip(users_data, users):
                    user_data['is_following'] = current_user.is_following(user_obj)
            else:
                for user_data in users_data:
                    user_data['is_following'] = False
            
            return {
                'users': users_data,
                'pagination': {
                    'total': paginated.total,
                    'pages': paginated.pages,
                    'page': paginated.page,
                    'per_page': paginated.per_page,
                    'next': paginated.next_num,
                    'prev': paginated.prev_num
                }
            }
        else:
            offset = (page - 1) * per_page
            users = query.offset(offset).limit(per_page).all()

            user_schema = UserSchema(many=True)
            schema_result = user_schema.dump(users)
            users_data = SocialService._handle_schema_result(schema_result)

            if current_user:
                for user_data, user_obj in zip(users_data, users):
                    user_data['is_following'] = current_user.is_following(user_obj)
            else:
                for user_data in users_data:
                    user_data['is_following'] = False
            
            return users_data

    @staticmethod
    def get_tags_data(current_user, search=None, filter_type=None, page=1, per_page=10, paginate=True):
        """Get tags data using schema methods for counts"""
        
        query = Tag.query.filter(Tag.deleted == False)
        
        if search and search.strip():
            query = query.filter(Tag.name.ilike(f'%{search}%'))

        if filter_type == 'trending':
            query = query.outerjoin(ProjectTag).group_by(Tag.id).order_by(
                desc(func.count(ProjectTag.tag_id))
            )
        elif filter_type == 'recently_updated':
            query = query.order_by(desc(Tag.updated_at))
        elif filter_type == 'newly_added':
            query = query.order_by(desc(Tag.date_created))
        else:
            query = query.order_by(desc(Tag.date_created))
        
        if paginate:
            paginated = query.paginate(page=page, per_page=per_page, error_out=False)
            tags = paginated.items

            tag_schema = TagSchema(many=True)
            schema_result = tag_schema.dump(tags)
            tags_data = SocialService._handle_schema_result(schema_result)
            
            return {
                'tags': tags_data,
                'pagination': {
                    'total': paginated.total,
                    'pages': paginated.pages,
                    'page': paginated.page,
                    'per_page': paginated.per_page,
                    'next': paginated.next_num,
                    'prev': paginated.prev_num
                }
            }
        else:
            offset = (page - 1) * per_page
            tags = query.offset(offset).limit(per_page).all()
            
            tag_schema = TagSchema(many=True)
            schema_result = tag_schema.dump(tags)
            tags_data = SocialService._handle_schema_result(schema_result)
            
            return tags_data

class SocialView(Resource):
    """
    Social View for browsing public projects, users, and tags
    
    GET /social?entity=projects&page=1&per_page=10&search=python&filter=trending
    GET /social?entity=users&page=1&per_page=10&search=john&filter=recently_updated
    GET /social?entity=tags&page=1&per_page=10&search=machine&filter=newly_added
    GET /social (returns all entities combined with distributed per_page)
    """
    
    def __init__(self):
        self.social_service = SocialService()
    
    @jwt_required
    def get(self):
        current_user_id = get_jwt_identity()
        current_user = User.get_by_id(current_user_id)
        
        if not current_user:
            return dict(status="fail", message="User not found"), 404

        entity = request.args.get('entity', '').lower()
        search = request.args.get('search', '').strip() or None
        filter_type = request.args.get('filter', '').lower() or None
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)

        # Validate pagination parameters
        per_page = max(1, min(per_page, 100))
        page = max(1, page)

        valid_entities = ['projects', 'users', 'tags']
        if entity and entity not in valid_entities:
            return dict(
                status="fail", 
                message=f"Invalid entity. Must be one of: {', '.join(valid_entities)}"
            ), 400

        valid_filters = ['trending', 'recently_updated', 'newly_added']
        if filter_type and filter_type not in valid_filters:
            return dict(
                status="fail", 
                message=f"Invalid filter. Must be one of: {', '.join(valid_filters)}"
            ), 400
        
        try:
            if entity:
                # Single entity request with pagination
                if entity == 'projects':
                    result = self.social_service.get_projects_data(
                        current_user, search, filter_type, page, per_page, paginate=True
                    )
                elif entity == 'users':
                    result = self.social_service.get_users_data(
                        current_user, search, filter_type, page, per_page, paginate=True
                    )
                elif entity == 'tags':
                    result = self.social_service.get_tags_data(
                        current_user, search, filter_type, page, per_page, paginate=True
                    )
                
                return dict(status='success', data=result), 200
            else:
                # All entities request - distribute per_page across entities
                items_per_entity = max(1, per_page // 3)
                
                # Get data for all entities (lists only, no pagination metadata)
                projects_data = self.social_service.get_projects_data(
                    current_user, search, filter_type, 
                    page=page, per_page=items_per_entity, paginate=False
                )
                users_data = self.social_service.get_users_data(
                    current_user, search, filter_type, 
                    page=page, per_page=items_per_entity, paginate=False
                )
                tags_data = self.social_service.get_tags_data(
                    current_user, search, filter_type, 
                    page=page, per_page=items_per_entity, paginate=False
                )

                # Limit each entity to the calculated items_per_entity
                projects_data = projects_data[:items_per_entity]
                users_data = users_data[:items_per_entity]
                tags_data = tags_data[:items_per_entity]
                
                # Calculate total items across all entities
                total_items = len(projects_data) + len(users_data) + len(tags_data)
                
                result = {
                    'projects': projects_data,
                    'users': users_data,
                    'tags': tags_data,
                    'pagination': {
                        'current_page': page,
                        'per_page': per_page,
                        'items_per_entity': items_per_entity,
                        'total_items': total_items,
                        'total_entities': 3
                    }
                }
                
                return dict(status='success', data=result), 200
                
        except Exception as e:
            return {"status":"fail", "message": f"An error occurred while fetching social data: {str(e)}"}, 500