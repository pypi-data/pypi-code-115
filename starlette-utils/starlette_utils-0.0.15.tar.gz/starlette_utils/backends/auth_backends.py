#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# @Time    : 2021/12/5 11:29 上午
# @Author  : Hubert Shelley
# @Project  : discussion-group
# @FileName: auth_backends.py
# @Software: PyCharm
"""
import binascii
from uuid import UUID

from starlette.authentication import AuthenticationBackend, AuthCredentials, AuthenticationError


# from common.sdk.base_sdk import AuthSDK


class User:
    def __init__(self, user_id, unit: str = None):
        if isinstance(user_id, UUID):
            self.id = user_id
        else:
            self.id = UUID(user_id)
        self.unit = unit
        self.is_authenticated = True


class AuthBackend(AuthenticationBackend):
    async def authenticate(self, request):
        if "Authorization" not in request.headers:
            return

        auth = request.headers["Authorization"]
        user: User = self.get_validated_token(auth)
        user.unit = request.headers.get('UNIT')

        return AuthCredentials(["authenticated"]), user

    def get_validated_token(self, raw_token):
        """
        Validates an encoded JSON web token and returns a validated token
        wrapper object.
        """
        try:
            # resp = AuthSDK.auth().token_check(raw_token)
            resp = {
                "user_id": '00000000-0000-0000-0000-000000000000'
            }
            return User(user_id=resp['user_id'])
        except Exception as e:
            raise AuthenticationError(e.__str__())
