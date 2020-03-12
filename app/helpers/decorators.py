from functools import wraps

from flask_jwt_extended import verify_jwt_in_request, get_jwt_claims

from .role_search import has_role


def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        claims = get_jwt_claims()
        if not has_role(claims['roles'], 'administrator'):
            return dict(status='fail', message='unauthorised'), 403
        return fn(*args, **kwargs)
    return wrapper
