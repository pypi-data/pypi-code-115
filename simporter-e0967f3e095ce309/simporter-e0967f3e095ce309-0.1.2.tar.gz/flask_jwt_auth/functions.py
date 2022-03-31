from typing import Optional, Any, Union, Dict
import jwt

from flask import request, current_app
from werkzeug.exceptions import Unauthorized, BadRequest, HTTPException


def decode_jwt_token(auth_token: str) -> Dict[str, Any]:
    """
    Decodes the auth token.
    """
    secret_key = current_app.config.get("JWT_SECRET_KEY", "default-secret-key")
    audience = current_app.config.get("JWT_AUDIENCE", "http://localhost:5000/")
    payload = jwt.decode(
        auth_token, secret_key, algorithms="HS256", audience=audience
    )
    return payload


def get_current_user() -> Optional[Union[str, int]]:
    """
    Get user data from the JWT token.

    :return: user identity (username or user id)
    """
    token = _get_token_from_headers()
    try:
        payload = _validate_jwt_token(token)
    except HTTPException:
        return
    return payload.get("sub")


def _get_token_from_headers() -> Optional[str]:
    """
    Get JWT token from headers.
    """
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.split()[1:]:
        return auth_header.split()[1]
    return


def _validate_jwt_token(auth_token: str) -> Dict[str, Any]:
    """
    Validate JWT token - check if exists, is not expired and invalid.
    """
    if auth_token is None:
        raise Unauthorized("Authentication required")
    try:
        payload = decode_jwt_token(auth_token)
    except jwt.ExpiredSignatureError:
        raise BadRequest("Signature expired. Please log in again")
    except jwt.InvalidTokenError:
        raise BadRequest("Invalid token. Please log in again")
    return payload
