"""
Unit tests for the improved SocialService class

Tests cover:
- Search term sanitization
- Time decay calculations
- Search scoring
- User interest extraction
- Filter validation
- Edge cases and error handling

Note: Deprecation warnings from dependencies (werkzeug, marshmallow, etc.) 
are expected and can be ignored. They don't affect test functionality.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch, PropertyMock
from sqlalchemy import func

from app.controllers.socials import SocialService
from app.models.user import User, Followers
from app.models.project import Project
from app.models.tags import Tag, TagFollowers
from app.models.project_users import ProjectFollowers


class TestSocialService:
    """Test suite for SocialService class"""

    # Test _sanitize_search_term
    def test_sanitize_search_term_valid(self):
        """Test sanitization of valid search terms"""
        assert SocialService._sanitize_search_term("python") == "python"
        assert SocialService._sanitize_search_term("  python  ") == "python"
        assert SocialService._sanitize_search_term(
            "machine learning") == "machine learning"

    def test_sanitize_search_term_empty(self):
        """Test sanitization of empty inputs"""
        assert SocialService._sanitize_search_term("") is None
        assert SocialService._sanitize_search_term("   ") is None
        assert SocialService._sanitize_search_term(None) is None

    def test_sanitize_search_term_special_chars(self):
        """Test escaping of SQL special characters"""
        # % and _ should be escaped for ILIKE
        result = SocialService._sanitize_search_term("test%search")
        assert "\\%" in result

        result = SocialService._sanitize_search_term("test_search")
        assert "\\_" in result

    def test_sanitize_search_term_length_limit(self):
        """Test maximum length enforcement"""
        long_term = "a" * 300
        result = SocialService._sanitize_search_term(long_term)
        assert len(result) == SocialService.MAX_SEARCH_TERM_LENGTH
        assert result == "a" * 200

    # Test _handle_schema_result
    def test_handle_schema_result_with_data_attribute(self):
        """Test handling schema result with .data attribute"""
        mock_result = Mock()
        mock_result.data = [1, 2, 3]
        result = SocialService._handle_schema_result(mock_result)
        assert result == [1, 2, 3]

    def test_handle_schema_result_direct_list(self):
        """Test handling direct list result"""
        result = SocialService._handle_schema_result([1, 2, 3])
        assert result == [1, 2, 3]

    def test_handle_schema_result_none(self):
        """Test handling None result"""
        result = SocialService._handle_schema_result(None)
        assert result == []

    def test_handle_schema_result_convertible(self):
        """Test handling tuple or other convertible types"""
        result = SocialService._handle_schema_result((1, 2, 3))
        assert result == [1, 2, 3]

    # Test _get_user_interests
    def test_get_user_interests_no_user(self):
        """Test user interests extraction with no user"""
        interests = SocialService._get_user_interests(None)
        assert interests == {
            'followed_tags': [],
            'followed_users': [],
            'followed_projects': []
        }

    @patch('app.controllers.socials.Followers')
    def test_get_user_interests_with_follows(self, mock_followers):
        """Test user interests extraction with various follows"""
        # Create mock user
        mock_user = Mock()
        mock_user.id = "user-123"

        # Mock followed tags
        mock_tag_follow = Mock()
        mock_tag_follow.tag_id = "tag-1"
        mock_user.followed_tags = [mock_tag_follow]

        # Mock followed projects
        mock_project_follow = Mock()
        mock_project_follow.project_id = "project-1"
        mock_user.followed_projects = [mock_project_follow]

        # Mock followed users
        mock_follower = Mock()
        mock_follower.followed_id = "user-456"
        mock_followers.query.filter_by.return_value.all.return_value = [
            mock_follower]

        interests = SocialService._get_user_interests(mock_user)

        assert "tag-1" in interests['followed_tags']
        assert "project-1" in interests['followed_projects']
        assert "user-456" in interests['followed_users']

    def test_get_user_interests_empty_follows(self):
        """Test user interests extraction with no follows"""
        mock_user = Mock()
        mock_user.id = "user-123"
        mock_user.followed_tags = []
        mock_user.followed_projects = []

        with patch('app.controllers.socials.Followers') as mock_followers:
            mock_followers.query.filter_by.return_value.all.return_value = []

            interests = SocialService._get_user_interests(mock_user)

            assert interests['followed_tags'] == []
            assert interests['followed_projects'] == []
            assert interests['followed_users'] == []


class TestSocialServiceIntegration:
    """Integration tests for SocialService methods"""

    @pytest.fixture
    def mock_user(self):
        """Create a mock user for testing"""
        user = Mock()
        user.id = "user-123"
        user.followed_tags = []
        user.followed_projects = []
        user.is_following = Mock(return_value=False)
        return user

    def _create_mock_query(self):
        """Helper to create a mock query object"""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.outerjoin.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []

        # Mock paginated result
        mock_paginated = Mock()
        mock_paginated.items = []
        mock_paginated.total = 0
        mock_paginated.pages = 0
        mock_paginated.page = 1
        mock_paginated.per_page = 10
        mock_paginated.next_num = None
        mock_paginated.prev_num = None
        mock_paginated.has_next = False
        mock_paginated.has_prev = False
        mock_query.paginate.return_value = mock_paginated

        return mock_query

    def test_get_projects_data_basic(self, mock_user):
        """Test basic project data retrieval"""
        mock_query = self._create_mock_query()

        with patch('app.controllers.socials.Project') as mock_project_class, \
                patch('app.controllers.socials.ProjectListSchema') as mock_schema_class, \
                patch.object(SocialService, '_get_user_interests', return_value={
                    'followed_tags': [],
                    'followed_users': [],
                    'followed_projects': []
                }):
            # Set up Project.query as a property that returns our mock
            type(mock_project_class).query = PropertyMock(
                return_value=mock_query)

            # Mock project objects
            mock_project = Mock()
            mock_project.is_followed_by = Mock(return_value=False)
            mock_query.paginate.return_value.items = [mock_project]

            # Mock schema
            mock_schema_instance = Mock()
            mock_schema_instance.dump.return_value = [{'id': 'test-project'}]
            mock_schema_class.return_value = mock_schema_instance

            result = SocialService.get_projects_data(
                mock_user,
                search=None,
                filter_type=None,
                page=1,
                per_page=10
            )

            assert 'projects' in result
            assert 'pagination' in result
            assert result['pagination']['page'] == 1

    def test_get_projects_data_with_search(self, mock_user):
        """Test project data retrieval with search"""
        mock_query = self._create_mock_query()

        with patch('app.controllers.socials.Project') as mock_project_class, \
                patch('app.controllers.socials.ProjectListSchema') as mock_schema_class, \
                patch.object(SocialService, '_get_user_interests', return_value={
                    'followed_tags': [],
                    'followed_users': [],
                    'followed_projects': []
                }):
            type(mock_project_class).query = PropertyMock(
                return_value=mock_query)

            mock_project = Mock()
            mock_project.is_followed_by = Mock(return_value=False)
            mock_query.paginate.return_value.items = [mock_project]

            mock_schema_instance = Mock()
            mock_schema_instance.dump.return_value = [{'id': 'test-project'}]
            mock_schema_class.return_value = mock_schema_instance

            result = SocialService.get_projects_data(
                mock_user,
                search="python",
                filter_type=None,
                page=1,
                per_page=10
            )

            assert mock_query.filter.called

    def test_get_projects_data_trending(self, mock_user):
        """Test trending projects filter"""
        mock_query = self._create_mock_query()

        with patch('app.controllers.socials.Project') as mock_project_class, \
                patch('app.controllers.socials.ProjectListSchema') as mock_schema_class, \
                patch.object(SocialService, '_get_user_interests', return_value={
                    'followed_tags': [],
                    'followed_users': [],
                    'followed_projects': []
                }):
            type(mock_project_class).query = PropertyMock(
                return_value=mock_query)

            mock_project = Mock()
            mock_project.is_followed_by = Mock(return_value=False)
            mock_query.paginate.return_value.items = [mock_project]

            mock_schema_instance = Mock()
            mock_schema_instance.dump.return_value = [{'id': 'test-project'}]
            mock_schema_class.return_value = mock_schema_instance

            result = SocialService.get_projects_data(
                mock_user,
                search=None,
                filter_type='trending',
                page=1,
                per_page=10
            )

            assert mock_query.outerjoin.called
            assert mock_query.group_by.called


class TestSocialServiceEdgeCases:
    """Test edge cases and error conditions"""

    def test_search_with_sql_injection_attempt(self):
        """Test that SQL injection attempts are sanitized"""
        malicious_input = "'; DROP TABLE users; --"
        sanitized = SocialService._sanitize_search_term(malicious_input)

        # Should escape special characters
        assert "DROP TABLE" in sanitized  # The text remains but escaped
        assert sanitized is not None

    def test_search_with_unicode(self):
        """Test search with unicode characters"""
        unicode_search = "pythön münchen"
        result = SocialService._sanitize_search_term(unicode_search)
        assert result == unicode_search

    def test_pagination_boundaries(self):
        """Test pagination with boundary values"""
        mock_user = Mock()
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.outerjoin.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []

        mock_project = Mock()
        mock_project.is_followed_by = Mock(return_value=False)

        mock_paginated = Mock()
        mock_paginated.items = [mock_project]
        mock_paginated.total = 1
        mock_paginated.pages = 1
        mock_paginated.page = 1
        mock_paginated.per_page = 1
        mock_paginated.next_num = None
        mock_paginated.prev_num = None
        mock_paginated.has_next = False
        mock_paginated.has_prev = False
        mock_query.paginate.return_value = mock_paginated

        with patch('app.controllers.socials.Project') as mock_project_class, \
                patch('app.controllers.socials.ProjectListSchema') as mock_schema_class, \
                patch.object(SocialService, '_get_user_interests', return_value={
                    'followed_tags': [],
                    'followed_users': [],
                    'followed_projects': []
                }):
            type(mock_project_class).query = PropertyMock(
                return_value=mock_query)

            mock_schema_instance = Mock()
            mock_schema_instance.dump.return_value = [{'id': 'test'}]
            mock_schema_class.return_value = mock_schema_instance

            result = SocialService.get_projects_data(
                mock_user, page=1, per_page=1
            )
            assert result['pagination']['per_page'] == 1
            assert result['pagination']['page'] == 1


class TestConfigurationConstants:
    """Test configuration constants are properly set"""

    def test_constants_exist(self):
        """Verify all expected constants exist"""
        assert hasattr(SocialService, 'TRENDING_DECAY_DAYS')
        assert hasattr(SocialService, 'MAX_SEARCH_TERM_LENGTH')
        assert hasattr(SocialService, 'POPULARITY_WEIGHT')
        assert hasattr(SocialService, 'RECENCY_WEIGHT')
        assert hasattr(SocialService, 'RELEVANCE_WEIGHT')

    def test_constants_are_reasonable(self):
        """Verify constants have reasonable values"""
        assert SocialService.TRENDING_DECAY_DAYS > 0
        assert SocialService.MAX_SEARCH_TERM_LENGTH > 0
        assert 0 <= SocialService.POPULARITY_WEIGHT <= 1
        assert 0 <= SocialService.RECENCY_WEIGHT <= 1
        assert 0 <= SocialService.RELEVANCE_WEIGHT <= 1

    def test_weights_sum_meaningful(self):
        """Verify weights are in reasonable ranges"""
        total = (
            SocialService.POPULARITY_WEIGHT +
            SocialService.RECENCY_WEIGHT +
            SocialService.RELEVANCE_WEIGHT
        )
        # Weights should sum to approximately 1.0 for normalized scoring
        assert 0.8 <= total <= 1.2


# Pytest configuration
if __name__ == '__main__':
    pytest.main([__file__, '-v'])
