# Social Discovery Algorithm

## Overview

The social discovery algorithm provides intelligent ranking and personalized recommendations for projects, users, and tags. It combines multiple signals (popularity, recency, relevance) to deliver better discovery experiences.

## How It Works

### Multi-Factor Scoring

The algorithm combines three main factors to rank content:

- **Popularity** (40%) - Follower/usage counts
- **Recency** (30%) - Time-decay for trending
- **Relevance** (30%) - Search match quality

### Trending Calculation

Uses time-decay to prevent stale content from dominating:

```python
# Projects
trending_score = (follower_count × 0.4) + (time_decay × 0.3)

# Users  
trending_score = (follower_count × 0.6) + (activity_decay × 0.4)

# Tags
trending_score = (project_count × 0.5) + (follower_count × 0.3) + (time_decay × 0.2)
```

**Time Decay Formula:** `score = 1.0 - (age_in_seconds / decay_period_seconds)` with minimum score of 0.1

### Personalized Recommendations

The `recommended` filter analyzes user behavior:

- Extracts user interests from followed tags, projects, and users
- Boosts content matching user's followed tags
- Excludes already-followed items
- Falls back to trending for new users with no follows

### Search Scoring

Search results are ranked by relevance:

- **Exact matches**: 10 points (highest priority)
- **Prefix matches**: 5 points
- **Contains matches**: 2 points
- Combined with popularity metrics for final ranking

Multi-field search across name, description, biography, and other relevant fields.

### Security

- Input sanitization prevents SQL injection
- Special characters (`%`, `_`) are escaped
- Maximum search term length: 200 characters
- All inputs validated before database queries

## Available Filters

### Projects

- `trending`, `recommended`, `recently_updated`, `newly_added`

### Users  

- `trending`, `recommended`, `recently_updated`, `newly_added`, `most_active`

### Tags

- `trending`, `recommended`, `recently_updated`, `newly_added`, `most_used`

## Configuration

Tunable parameters in `app/controllers/socials.py`:

```python
TRENDING_DECAY_DAYS = 30      # Days for time-decay window
MAX_SEARCH_TERM_LENGTH = 200  # Maximum search term length
POPULARITY_WEIGHT = 0.4       # Weight for popularity
RECENCY_WEIGHT = 0.3          # Weight for recency
RELEVANCE_WEIGHT = 0.3        # Weight for search relevance
```

## Links

- **API Documentation**: See [`api_docs.yml`](../api_docs.yml#L4256) for full endpoint details
- **Implementation**: [`app/controllers/socials.py`](../app/controllers/socials.py)
- **Tests**: [`app/tests/social/test_social_service.py`](../app/tests/social/test_social_service.py)

## Testing

```bash
# Run tests
pytest app/tests/social/test_social_service.py -v

# With coverage
pytest app/tests/social/ --cov=app.controllers.socials --cov-report=html
```

## Performance

**Target Metrics:**

- Simple queries: < 100ms
- Search queries: < 200ms
- Trending calculations: < 300ms

**Recommended Database Indexes:**

```sql
CREATE INDEX idx_project_public_status ON project(is_public, deleted, disabled);
CREATE INDEX idx_user_public_verified ON "user"(is_public, verified, disabled);
CREATE INDEX idx_tag_deleted ON tag(deleted);
CREATE INDEX idx_project_followers_project ON project_followers(project_id);
CREATE INDEX idx_followers_followed ON followers(followed_id);
```

---
