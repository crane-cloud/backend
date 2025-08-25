# app/views/social.py
from app.helpers.socials import get_projects_data, get_tags_data, get_users_data
from flask import request
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.models.user import User


class SocialView(Resource):
    """
    Social View for browsing public projects, users, and tags
    
    GET /social?entity=projects&page=1&per_page=10&search=python&filter=trending
    GET /social?entity=users&page=1&per_page=10&search=john&filter=recently_updated
    GET /social?entity=tags&page=1&per_page=10&search=machine&filter=newly_added
    GET /social (returns all entities combined)
    """
    
    @jwt_required
    def get(self):
        # Get current logged-in user
        current_user_id = get_jwt_identity()
        current_user = User.get_by_id(current_user_id)
        
        if not current_user:
            return dict(status="fail", message="User not found"), 404

        # Get query parameters
        entity = request.args.get('entity', '').lower()
        search = request.args.get('search', '').strip() or None
        filter_type = request.args.get('filter', '').lower() or None
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # Validate per_page limits
        if per_page > 100:
            per_page = 100
        elif per_page < 1:
            per_page = 10
            
        # Validate page
        if page < 1:
            page = 1
        
        # Validate entity parameter
        valid_entities = ['projects', 'users', 'tags']
        if entity and entity not in valid_entities:
            return dict(
                status="fail", 
                message=f"Invalid entity. Must be one of: {', '.join(valid_entities)}"
            ), 400
        
        # Validate filter parameter
        valid_filters = ['trending', 'recently_updated', 'newly_added']
        if filter_type and filter_type not in valid_filters:
            return dict(
                status="fail", 
                message=f"Invalid filter. Must be one of: {', '.join(valid_filters)}"
            ), 400
        
        try:
            if entity:
                if entity == 'projects':
                    result = get_projects_data(current_user, search, filter_type, page, per_page)
                elif entity == 'users':
                    result = get_users_data(current_user, search, filter_type, page, per_page)
                elif entity == 'tags':
                    result = get_tags_data(current_user, search, filter_type, page, per_page)
                
                return dict(status='success', data=result), 200
            else:
                combined_per_page = per_page
 
                projects_list = get_projects_data(
                    current_user, search, filter_type, 
                    page=page, per_page=combined_per_page, paginate=False
                )
                users_list = get_users_data(
                    current_user, search, filter_type, 
                    page=page, per_page=combined_per_page, paginate=False
                )
                tags_list = get_tags_data(
                    current_user, search, filter_type, 
                    page=page, per_page=combined_per_page, paginate=False
                )
                
                # Ensure we have lists
                if not isinstance(projects_list, list):
                    projects_list = []
                if not isinstance(users_list, list):
                    users_list = []
                if not isinstance(tags_list, list):
                    tags_list = []
  
                # Calculate total counts for proper pagination
                total_projects = len(projects_list)
                total_users = len(users_list)
                total_tags = len(tags_list)
                total_items = total_projects + total_users + total_tags
                
                result = {
                    'projects': projects_list,
                    'users': users_list,
                    'tags': tags_list,
                    'pagination': {
                        'total': total_items,
                        'pages': None,  
                        'page': page,
                        'per_page': per_page * 3,  
                        'next': None,  
                        'prev': None   
                    }
                }
                
                return dict(status='success', data=result), 200
                
        except Exception as e:
             return {"status":"fail", "message": f"An error occurred while fetching social data: {str(e)}"}, 500