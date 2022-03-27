import time

import jwt

from requests.auth import AuthBase


class JWTAuth(AuthBase):
    def __init__(self, username, passowrd, create_token_func, check_token_func=None, header_name="Authorization", header_fmt="Bearer {}"):
        self.username = username
        self.password = passowrd
        self.create_token_func = create_token_func
        self.check_token_func = check_token_func or self._check_token_func
        self.token = create_token_func(username, passowrd)
        self.header_name = header_name
        self.header_fmt = header_fmt
    
    def _check_token_func(self, token):
        try:
            payload = jwt.decode(token, options={"verify_signature": False})
        except Exception as e:
            return False
        if payload.get("exp") - time.time() < 60:
            return False
        return True

    def __call__(self, r):
        if not self.check_token_func:
            self.token = self.create_token_func()
        r.headers[self.header_name] = self.header_fmt.format(self.token)
        return r
