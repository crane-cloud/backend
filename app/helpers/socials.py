# app/helpers/social.py
from sqlalchemy import or_, desc, func
from app.models.user import User, Followers
from app.models.project import Project
from app.models.tags import Tag, TagFollowers, ProjectTag
from app.models.project_users import ProjectFollowers, ProjectUser
from app.schemas.user import UserSchema
from app.schemas.project import ProjectSchema
from app.schemas.tags import TagSchema


def get_projects_data(current_user, search=None, filter_type=None, page=1, per_page=10, paginate=True):
 
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
    else:
        offset = (page - 1) * per_page
        projects = query.offset(offset).limit(per_page).all()
    
    project_schema = ProjectSchema(many=True)
    schema_result = project_schema.dump(projects)

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
    
    # Add additional counts to each project
    for i, project in enumerate(projects):
        if i < len(projects_data) and isinstance(projects_data[i], dict):
            try:
                followers_count = ProjectFollowers.query.filter_by(project_id=project.id).count()
                projects_data[i]['followers_count'] = followers_count

                tags_count = ProjectTag.query.filter_by(project_id=project.id).count()
                projects_data[i]['tags_count'] = tags_count

                members_count = ProjectUser.query.filter_by(project_id=project.id).count()
                projects_data[i]['members_count'] = members_count

                if current_user:
                    try:
                        is_following = project.is_followed_by(current_user)
                        projects_data[i]['is_following'] = is_following
                    except Exception:
                        projects_data[i]['is_following'] = False
                else:
                    projects_data[i]['is_following'] = False
                    
            except Exception:
                projects_data[i]['followers_count'] = 0
                projects_data[i]['tags_count'] = 0
                projects_data[i]['members_count'] = 0
                projects_data[i]['is_following'] = False
    
    if paginate:
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
        return projects_data


def get_users_data(current_user, search=None, filter_type=None, page=1, per_page=10, paginate=True):

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
    else:
        offset = (page - 1) * per_page
        users = query.offset(offset).limit(per_page).all()

    user_schema = UserSchema(many=True)
    schema_result = user_schema.dump(users)
    
    # Extract data from MarshalResult object
    if hasattr(schema_result, 'data'):
        users_data = schema_result.data
    else:
        users_data = schema_result

    # Check if schema returned None or invalid data
    if users_data is None:
        users_data = []
    elif not isinstance(users_data, list):
        try:
            users_data = list(users_data)
        except:
            users_data = []

    # Add follower and additional information for each PUBLIC user
    for i, user in enumerate(users):
        if i < len(users_data) and isinstance(users_data[i], dict):
            try:
                followers_count = Followers.query.filter_by(followed_id=user.id).count()
                users_data[i]['followers_count'] = followers_count

                following_count = Followers.query.filter_by(follower_id=user.id).count()
                users_data[i]['following_count'] = following_count

                owned_projects_count = Project.query.filter_by(
                    owner_id=user.id,
                    deleted=False,
                    disabled=False,
                    admin_disabled=False,
                    is_public=True
                ).count()
                users_data[i]['owned_projects_count'] = owned_projects_count
        
                collaborative_projects_count = ProjectUser.query.filter_by(user_id=user.id).count()
                users_data[i]['collaborative_projects_count'] = collaborative_projects_count
                
                followed_tags_count = TagFollowers.query.filter_by(user_id=user.id).count()
                users_data[i]['followed_tags_count'] = followed_tags_count

                followed_projects_count = ProjectFollowers.query.filter_by(user_id=user.id).count()
                users_data[i]['followed_projects_count'] = followed_projects_count

                if current_user:
                    try:
                        is_following = current_user.is_following(user)
                        users_data[i]['is_following'] = is_following
                    except Exception:
                        users_data[i]['is_following'] = False
                else:
                    users_data[i]['is_following'] = False
                
            except Exception:
                users_data[i]['followers_count'] = 0
                users_data[i]['following_count'] = 0
                users_data[i]['owned_projects_count'] = 0
                users_data[i]['collaborative_projects_count'] = 0
                users_data[i]['followed_tags_count'] = 0
                users_data[i]['followed_projects_count'] = 0
                users_data[i]['is_following'] = False
    
    if paginate:
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
        return users_data


def get_tags_data(current_user, search=None, filter_type=None, page=1, per_page=10, paginate=True):

    query = Tag.query.filter(Tag.deleted == False)
    
    if search and search.strip():
        query = query.filter(Tag.name.ilike(f'%{search}%'))

    if filter_type == 'trending':
        query = query.outerjoin(TagFollowers).group_by(Tag.id).order_by(
            desc(func.count(TagFollowers.id))
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
    else:
        offset = (page - 1) * per_page
        tags = query.offset(offset).limit(per_page).all()
    
    tag_schema = TagSchema(many=True)
    schema_result = tag_schema.dump(tags)
    
    # Extract data from MarshalResult object
    if hasattr(schema_result, 'data'):
        tags_data = schema_result.data
    else:
        tags_data = schema_result
 
    if tags_data is None:
        tags_data = []
    elif not isinstance(tags_data, list):
        try:
            tags_data = list(tags_data)
        except:
            tags_data = []

    # Add additional counts to each tag
    for i, tag in enumerate(tags):
        if i < len(tags_data) and isinstance(tags_data[i], dict):
            try:
 
                project_tags_count = ProjectTag.query.filter_by(tag_id=tag.id).count()
                tags_data[i]['project_tags_count'] = project_tags_count

                followers_count = TagFollowers.query.filter_by(tag_id=tag.id).count()
                tags_data[i]['followers_count'] = followers_count

                if current_user:
                    is_following = TagFollowers.query.filter_by(
                        user_id=current_user.id, 
                        tag_id=tag.id
                    ).first() is not None
                    tags_data[i]['is_following'] = is_following
                else:
                    tags_data[i]['is_following'] = False
                    
            except Exception:
                tags_data[i]['project_tags_count'] = 0
                tags_data[i]['followers_count'] = 0
                tags_data[i]['is_following'] = False

    if paginate:
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
        return tags_data