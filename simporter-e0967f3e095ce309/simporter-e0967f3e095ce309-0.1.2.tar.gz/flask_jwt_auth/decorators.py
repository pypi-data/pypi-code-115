from functools import wraps
from typing import Callable

from flask_jwt_auth.functions import _get_token_from_headers, \
    _validate_jwt_token


def jwt_required(func: Callable) -> Callable:
    """
    Decorator to check token existing and validate it.
    """
    @wraps(func)
    def wrapper(*args, **kwargs) -> Callable:
        token = _get_token_from_headers()
        _validate_jwt_token(token)
        return func(*args, **kwargs)
    return wrapper
