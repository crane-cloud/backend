from flask import request
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import or_, desc, func, case, cast, Float, and_
from sqlalchemy.sql import text
from datetime import datetime, timedelta
import re

from app.models.user import User, Followers
from app.models.project import Project
from app.models.tags import ProjectTag, Tag, TagFollowers
from app.models.project_users import ProjectFollowers
from app.schemas.user import SimpleUserSchema
from app.schemas.project import ProjectListSchema
from app.schemas.tags import TagSchema


class SocialService:
    """Service class for handling social data operations with advanced ranking algorithms"""

    # Configuration constants
    TRENDING_DECAY_DAYS = 30  # Days over which engagement decays
    MAX_SEARCH_TERM_LENGTH = 200  # Prevent performance issues
    POPULARITY_WEIGHT = 0.4
    RECENCY_WEIGHT = 0.3
    RELEVANCE_WEIGHT = 0.3

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
            except Exception:
                data = []

        return data

    @staticmethod
    def _sanitize_search_term(search_term):
        """Sanitize and validate search input to prevent SQL injection and improve performance"""
        if not search_term:
            return None

        # Strip whitespace
        sanitized = search_term.strip()

        # Limit length to prevent performance issues
        if len(sanitized) > SocialService.MAX_SEARCH_TERM_LENGTH:
            sanitized = sanitized[:SocialService.MAX_SEARCH_TERM_LENGTH]

        # Escape special regex characters for ILIKE
        sanitized = re.sub(r'[%_]', r'\\\g<0>', sanitized)

        return sanitized if sanitized else None

    @staticmethod
    def _calculate_time_decay_score(date_field, decay_days=TRENDING_DECAY_DAYS):
        """
        Calculate a time decay score for trending calculations.
        Returns a value between 0 and 1, where newer items score higher.
        """
        now = datetime.utcnow()
        decay_start = now - timedelta(days=decay_days)

        return case(
            (date_field >= decay_start,
             1.0 - (cast(func.extract('epoch', now - date_field), Float) /
                    (decay_days * 86400.0))
             ),
            else_=0.1  # Minimum score for old items
        )

    @staticmethod
    def _get_user_interests(user):
        """Extract user interests based on their follows and interactions"""
        if not user:
            return {'followed_tags': [], 'followed_users': [], 'followed_projects': []}

        # Get tags from followed projects
        followed_tag_ids = [
            tag.tag_id for tag in user.followed_tags] if user.followed_tags else []
        followed_user_ids = [
            f.followed_id for f in Followers.query.filter_by(follower_id=user.id).all()]
        followed_project_ids = [
            fp.project_id for fp in user.followed_projects] if user.followed_projects else []

        return {
            'followed_tags': followed_tag_ids,
            'followed_users': followed_user_ids,
            'followed_projects': followed_project_ids
        }

    @staticmethod
    def _build_search_score(search_term, *fields):
        """
        Build a relevance score for search across multiple fields.
        Exact matches score higher than partial matches.
        """
        if not search_term:
            return 0

        score_cases = []
        search_lower = search_term.lower()

        for field in fields:
            # Exact match (case-insensitive): highest score
            score_cases.append(
                case((func.lower(field) == search_lower, 10), else_=0)
            )
            # Starts with search term: high score
            score_cases.append(
                case((func.lower(field).like(f'{search_lower}%'), 5), else_=0)
            )
            # Contains search term: medium score
            score_cases.append(
                case((func.lower(field).like(f'%{search_lower}%'), 2), else_=0)
            )

        # Sum all score components
        total_score = sum(score_cases) if score_cases else 0
        return total_score

    @staticmethod
    def get_projects_data(current_user, search=None, filter_type=None, page=1, per_page=10, paginate=True):
        """
        Get projects data with advanced ranking algorithm.

        Supports personalized recommendations based on user interests,
        sophisticated trending calculations with time decay, and
        weighted search relevance scoring.
        """
        # Sanitize search input
        search = SocialService._sanitize_search_term(search)

        # Get user interests for personalization
        user_interests = SocialService._get_user_interests(current_user)

        # Base query with quality filters
        query = Project.query.filter(
            Project.deleted == False,
            Project.disabled == False,
            Project.admin_disabled == False,
            Project.is_public == True
        )

        # Exclude projects already followed by user (for discovery)
        if current_user and filter_type == 'recommended':
            query = query.filter(
                ~Project.id.in_(user_interests['followed_projects'])
            )

        # Apply search filter with relevance scoring
        if search:
            search_filter = or_(
                Project.name.ilike(f'%{search}%'),
                Project.description.ilike(f'%{search}%'),
                Project.alias.ilike(f'%{search}%')
            )
            query = query.filter(search_filter)

        # Join tables for ranking calculations
        query = query.outerjoin(ProjectFollowers)
        query = query.outerjoin(ProjectTag)
        query = query.group_by(Project.id)

        # Apply ordering based on filter type
        if filter_type == 'trending':
            # Advanced trending: combines follower count with time decay
            time_decay = SocialService._calculate_time_decay_score(
                Project.updated_at)
            follower_count = func.count(func.distinct(ProjectFollowers.id))

            trending_score = (
                (follower_count * SocialService.POPULARITY_WEIGHT) +
                (time_decay * SocialService.RECENCY_WEIGHT)
            )
            query = query.order_by(desc(trending_score),
                                   desc(Project.date_created))

        elif filter_type == 'recommended':
            # Personalized recommendations based on user's followed tags
            if user_interests['followed_tags']:
                # Boost projects with tags the user follows
                tag_match_score = func.sum(
                    case((ProjectTag.tag_id.in_(
                        user_interests['followed_tags']), 5), else_=0)
                )
                follower_count = func.count(func.distinct(ProjectFollowers.id))
                recency_score = SocialService._calculate_time_decay_score(
                    Project.date_created)

                recommendation_score = (
                    (tag_match_score * 0.5) +
                    (follower_count * 0.3) +
                    (recency_score * 0.2)
                )
                query = query.order_by(
                    desc(recommendation_score), desc(Project.updated_at))
            else:
                # Fallback to trending for users with no interests
                follower_count = func.count(func.distinct(ProjectFollowers.id))
                query = query.order_by(
                    desc(follower_count), desc(Project.date_created))

        elif filter_type == 'recently_updated':
            query = query.order_by(desc(Project.updated_at))

        elif filter_type == 'newly_added':
            query = query.order_by(desc(Project.date_created))

        elif search:
            # Search mode: rank by relevance
            search_score = SocialService._build_search_score(
                search, Project.name, Project.description, Project.alias
            )
            follower_count = func.count(func.distinct(ProjectFollowers.id))

            combined_score = (
                (search_score * SocialService.RELEVANCE_WEIGHT) +
                (follower_count * SocialService.POPULARITY_WEIGHT)
            )
            query = query.order_by(desc(combined_score),
                                   desc(Project.updated_at))
        else:
            # Default: newest first
            query = query.order_by(desc(Project.date_created))

        # Execute query with pagination
        if paginate:
            paginated = query.paginate(
                page=page, per_page=per_page, error_out=False)
            projects = paginated.items

            project_schema = ProjectListSchema(many=True)
            schema_result = project_schema.dump(projects)
            projects_data = SocialService._handle_schema_result(schema_result)

            # Add follow status for current user
            if current_user:
                for project_data, project_obj in zip(projects_data, projects):
                    project_data['is_following'] = project_obj.is_followed_by(
                        current_user)

            return {
                'projects': projects_data,
                'pagination': {
                    'total': paginated.total,
                    'pages': paginated.pages,
                    'page': paginated.page,
                    'per_page': paginated.per_page,
                    'next': paginated.next_num,
                    'prev': paginated.prev_num,
                    'has_next': paginated.has_next,
                    'has_prev': paginated.has_prev
                }
            }
        else:
            offset = (page - 1) * per_page
            projects = query.offset(offset).limit(per_page).all()

            project_schema = ProjectListSchema(many=True)
            schema_result = project_schema.dump(projects)
            projects_data = SocialService._handle_schema_result(schema_result)

            # Add follow status for current user
            if current_user:
                for project_data, project_obj in zip(projects_data, projects):
                    project_data['is_following'] = project_obj.is_followed_by(
                        current_user)

            return projects_data

    @staticmethod
    def get_users_data(current_user, search=None, filter_type=None, page=1, per_page=10, paginate=True):
        """
        Get users data with advanced ranking algorithm.

        Supports personalized recommendations based on network connections,
        activity recency, and engagement metrics.
        """
        # Sanitize search input
        search = SocialService._sanitize_search_term(search)

        # Get user interests for personalization
        user_interests = SocialService._get_user_interests(current_user)

        # Base query with quality filters
        query = User.query.filter(
            User.disabled == False,
            User.admin_disabled == False,
            User.is_public == True,
            User.verified == True
        )

        # Exclude current user and already followed users
        if current_user:
            exclude_ids = [current_user.id] + user_interests['followed_users']
            query = query.filter(~User.id.in_(exclude_ids))

        # Apply search filter
        if search:
            search_filter = or_(
                User.name.ilike(f'%{search}%'),
                User.username.ilike(f'%{search}%'),
                User.biography.ilike(f'%{search}%'),
                User.organisation.ilike(f'%{search}%')
            )
            query = query.filter(search_filter)

        # Join for follower counts
        query = query.outerjoin(Followers, Followers.followed_id == User.id)
        query = query.group_by(User.id)

        # Apply ordering based on filter type
        if filter_type == 'trending':
            # Advanced trending: combines followers with recent activity
            follower_count = func.count(func.distinct(Followers.follower_id))
            activity_decay = SocialService._calculate_time_decay_score(
                User.last_seen, decay_days=7)

            trending_score = (
                (follower_count * 0.6) +
                (activity_decay * 10 * 0.4)  # Scale activity to similar range
            )
            query = query.order_by(desc(trending_score), desc(User.last_seen))

        elif filter_type == 'recommended':
            # Recommend users who follow similar projects/tags
            if user_interests['followed_tags'] or user_interests['followed_projects']:
                # This would require a more complex subquery to find users with similar interests
                # For now, use a combination of follower count and activity
                follower_count = func.count(
                    func.distinct(Followers.follower_id))
                activity_score = SocialService._calculate_time_decay_score(
                    User.last_seen, decay_days=14)

                recommendation_score = (
                    (follower_count * 0.4) +
                    (activity_score * 10 * 0.6)
                )
                query = query.order_by(
                    desc(recommendation_score), desc(User.date_created))
            else:
                # Fallback to active users
                query = query.order_by(desc(User.last_seen))

        elif filter_type == 'recently_updated':
            # Most recently active users
            query = query.order_by(desc(User.last_seen),
                                   desc(User.date_created))

        elif filter_type == 'newly_added':
            # Newest users
            query = query.order_by(desc(User.date_created))

        elif filter_type == 'most_active':
            # Most active users (by last_seen)
            query = query.filter(
                User.last_seen >= datetime.utcnow() - timedelta(days=30)
            ).order_by(desc(User.last_seen))

        elif search:
            # Search mode: rank by relevance and popularity
            search_score = SocialService._build_search_score(
                search, User.name, User.username, User.biography, User.organisation
            )
            follower_count = func.count(func.distinct(Followers.follower_id))

            combined_score = (
                (search_score * 0.6) +
                (follower_count * 0.4)
            )
            query = query.order_by(desc(combined_score), desc(User.last_seen))
        else:
            # Default: newest users first
            query = query.order_by(desc(User.date_created))

        # Execute query with pagination
        if paginate:
            paginated = query.paginate(
                page=page, per_page=per_page, error_out=False)
            users = paginated.items

            user_schema = SimpleUserSchema(many=True)
            schema_result = user_schema.dump(users)
            users_data = SocialService._handle_schema_result(schema_result)

            # Add follow status
            if current_user:
                for user_data, user_obj in zip(users_data, users):
                    user_data['is_following'] = current_user.is_following(
                        user_obj)
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
                    'prev': paginated.prev_num,
                    'has_next': paginated.has_next,
                    'has_prev': paginated.has_prev
                }
            }
        else:
            offset = (page - 1) * per_page
            users = query.offset(offset).limit(per_page).all()

            user_schema = SimpleUserSchema(many=True)
            schema_result = user_schema.dump(users)
            users_data = SocialService._handle_schema_result(schema_result)

            if current_user:
                for user_data, user_obj in zip(users_data, users):
                    user_data['is_following'] = current_user.is_following(
                        user_obj)
            else:
                for user_data in users_data:
                    user_data['is_following'] = False

            return users_data

    @staticmethod
    def get_tags_data(current_user, search=None, filter_type=None, page=1, per_page=10, paginate=True):
        """
        Get tags data with advanced ranking algorithm.

        Supports trending calculations based on project associations,
        tag follower counts, and recency.
        """
        # Sanitize search input
        search = SocialService._sanitize_search_term(search)

        # Get user interests for personalization
        user_interests = SocialService._get_user_interests(current_user)

        # Base query
        query = Tag.query.filter(Tag.deleted == False)

        # Apply search filter
        if search:
            query = query.filter(Tag.name.ilike(f'%{search}%'))

        # Exclude tags already followed (for discovery)
        if current_user and filter_type == 'recommended':
            query = query.filter(~Tag.id.in_(user_interests['followed_tags']))

        # Join tables for ranking
        query = query.outerjoin(ProjectTag)
        query = query.outerjoin(TagFollowers)
        query = query.group_by(Tag.id)

        # Apply ordering based on filter type
        if filter_type == 'trending':
            # Advanced trending: project count + follower count + time decay
            project_count = func.count(func.distinct(ProjectTag.project_id))
            follower_count = func.count(func.distinct(TagFollowers.id))
            time_decay = SocialService._calculate_time_decay_score(
                Tag.updated_at, decay_days=60)

            trending_score = (
                (project_count * 0.5) +
                (follower_count * 0.3) +
                (time_decay * 10 * 0.2)
            )
            query = query.order_by(desc(trending_score),
                                   desc(Tag.date_created))

        elif filter_type == 'recommended':
            # Recommend tags based on user's project follows
            project_count = func.count(func.distinct(ProjectTag.project_id))
            follower_count = func.count(func.distinct(TagFollowers.id))

            # Boost super tags
            super_tag_boost = case((Tag.is_super_tag == True, 5), else_=0)

            recommendation_score = (
                (project_count * 0.4) +
                (follower_count * 0.3) +
                (super_tag_boost * 0.3)
            )
            query = query.order_by(
                desc(recommendation_score), desc(Tag.updated_at))

        elif filter_type == 'recently_updated':
            query = query.order_by(desc(Tag.updated_at),
                                   desc(Tag.date_created))

        elif filter_type == 'newly_added':
            query = query.order_by(desc(Tag.date_created))

        elif filter_type == 'most_used':
            # Tags with most projects
            project_count = func.count(func.distinct(ProjectTag.project_id))
            query = query.order_by(desc(project_count), desc(Tag.date_created))

        elif search:
            # Search mode: exact match prioritization
            search_score = SocialService._build_search_score(search, Tag.name)
            project_count = func.count(func.distinct(ProjectTag.project_id))

            combined_score = (
                (search_score * 0.7) +
                (project_count * 0.3)
            )
            query = query.order_by(desc(combined_score),
                                   desc(Tag.date_created))
        else:
            # Default: most used tags
            project_count = func.count(func.distinct(ProjectTag.project_id))
            query = query.order_by(desc(project_count), desc(Tag.date_created))

        # Execute query with pagination
        if paginate:
            paginated = query.paginate(
                page=page, per_page=per_page, error_out=False)
            tags = paginated.items

            tag_schema = TagSchema(many=True)
            schema_result = tag_schema.dump(tags)
            tags_data = SocialService._handle_schema_result(schema_result)

            # Add follow status for current user
            if current_user:
                for tag_data, tag_obj in zip(tags_data, tags):
                    tag_data['is_following'] = any(
                        tf.user_id == current_user.id for tf in tag_obj.followers
                    )
            else:
                for tag_data in tags_data:
                    tag_data['is_following'] = False

            return {
                'tags': tags_data,
                'pagination': {
                    'total': paginated.total,
                    'pages': paginated.pages,
                    'page': paginated.page,
                    'per_page': paginated.per_page,
                    'next': paginated.next_num,
                    'prev': paginated.prev_num,
                    'has_next': paginated.has_next,
                    'has_prev': paginated.has_prev
                }
            }
        else:
            offset = (page - 1) * per_page
            tags = query.offset(offset).limit(per_page).all()

            tag_schema = TagSchema(many=True)
            schema_result = tag_schema.dump(tags)
            tags_data = SocialService._handle_schema_result(schema_result)

            # Add follow status for current user
            if current_user:
                for tag_data, tag_obj in zip(tags_data, tags):
                    tag_data['is_following'] = any(
                        tf.user_id == current_user.id for tf in tag_obj.followers
                    )
            else:
                for tag_data in tags_data:
                    tag_data['is_following'] = False

            return tags_data


class SocialView(Resource):
    """
    Enhanced Social View for browsing public projects, users, and tags.

    Supports advanced filtering, personalized recommendations, and sophisticated ranking.

    Query Parameters:
        - entity: Type of content to fetch (projects|users|tags). Omit for all entities.
        - page: Page number (default: 1, min: 1)
        - per_page: Items per page (default: 10, min: 1, max: 100)
        - search: Search term for filtering content
        - filter: Sorting/filtering strategy

    Filter Options:
        - trending: Time-decayed engagement-based ranking
        - recommended: Personalized suggestions based on user interests
        - recently_updated: Most recently updated items
        - newly_added: Newest items first
        - most_active: Most active users (users only)
        - most_used: Most used tags (tags only)

    Examples:
        GET /social?entity=projects&filter=trending&page=1&per_page=20
        GET /social?entity=users&filter=recommended&search=developer
        GET /social?entity=tags&filter=most_used
        GET /social (returns all entities with distributed pagination)
    """

    # Valid filter types per entity
    VALID_FILTERS = {
        'projects': ['trending', 'recommended', 'recently_updated', 'newly_added'],
        'users': ['trending', 'recommended', 'recently_updated', 'newly_added', 'most_active'],
        'tags': ['trending', 'recommended', 'recently_updated', 'newly_added', 'most_used'],
        # For combined entity queries
        'all': ['trending', 'recently_updated', 'newly_added']
    }

    def __init__(self):
        self.social_service = SocialService()

    @jwt_required
    def get(self):
        """Handle GET requests for social data discovery"""
        try:
            # Get and validate current user
            current_user_id = get_jwt_identity()
            current_user = User.get_by_id(current_user_id)

            if not current_user:
                return dict(status="fail", message="User not found"), 404

            # Extract and validate query parameters
            entity = request.args.get('entity', '').lower() or None
            search = request.args.get('search', '').strip() or None
            filter_type = request.args.get('filter', '').lower() or None

            # Pagination parameters with bounds
            page = max(1, request.args.get('page', 1, type=int))
            per_page = max(1, min(request.args.get(
                'per_page', 10, type=int), 100))

            # Validate entity parameter
            valid_entities = ['projects', 'users', 'tags']
            if entity and entity not in valid_entities:
                return dict(
                    status="fail",
                    message=f"Invalid entity. Must be one of: {', '.join(valid_entities)}"
                ), 400

            # Validate filter parameter based on entity
            filter_context = entity if entity else 'all'
            valid_filters = self.VALID_FILTERS.get(filter_context, [])

            if filter_type and filter_type not in valid_filters:
                return dict(
                    status="fail",
                    message=f"Invalid filter for {filter_context}. Must be one of: {', '.join(valid_filters)}"
                ), 400

            # Validate search term length
            if search and len(search) > SocialService.MAX_SEARCH_TERM_LENGTH:
                return dict(
                    status="fail",
                    message=f"Search term too long. Maximum length is {SocialService.MAX_SEARCH_TERM_LENGTH} characters."
                ), 400

            # Process request based on entity type
            if entity:
                # Single entity request with full pagination
                result = self._fetch_single_entity(
                    entity, current_user, search, filter_type, page, per_page
                )
                return dict(status='success', data=result), 200
            else:
                # Multi-entity request with distributed pagination
                result = self._fetch_all_entities(
                    current_user, search, filter_type, page, per_page
                )
                return dict(status='success', data=result), 200

        except ValueError as e:
            # Handle validation errors
            return dict(status="fail", message=str(e)), 400
        except Exception as e:
            # Handle unexpected errors with logging
            import traceback
            error_trace = traceback.format_exc()
            # In production, log error_trace to your logging system
            return dict(
                status="fail",
                message="An error occurred while fetching social data. Please try again."
            ), 500

    def _fetch_single_entity(self, entity, current_user, search, filter_type, page, per_page):
        """Fetch data for a single entity type"""
        if entity == 'projects':
            return self.social_service.get_projects_data(
                current_user, search, filter_type, page, per_page, paginate=True
            )
        elif entity == 'users':
            return self.social_service.get_users_data(
                current_user, search, filter_type, page, per_page, paginate=True
            )
        elif entity == 'tags':
            return self.social_service.get_tags_data(
                current_user, search, filter_type, page, per_page, paginate=True
            )

    def _fetch_all_entities(self, current_user, search, filter_type, page, per_page):
        """Fetch data for all entity types with distributed pagination"""
        # Distribute per_page across three entity types
        items_per_entity = max(1, per_page // 3)

        # Fetch data for all entities (without full pagination metadata)
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

        # Limit results to calculated items per entity
        projects_data = projects_data[:items_per_entity]
        users_data = users_data[:items_per_entity]
        tags_data = tags_data[:items_per_entity]

        # Calculate totals
        total_items = len(projects_data) + len(users_data) + len(tags_data)

        return {
            'projects': projects_data,
            'users': users_data,
            'tags': tags_data,
            'pagination': {
                'current_page': page,
                'per_page': per_page,
                'items_per_entity': items_per_entity,
                'total_items': total_items,
                'total_entities': 3
            },
            'metadata': {
                'filter_applied': filter_type,
                'search_term': search
            }
        }
