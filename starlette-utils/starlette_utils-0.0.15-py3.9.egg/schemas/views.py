#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# @Time    : 2021/9/5 19:39
# @Author  : Hubert Shelley
# @Project  : microservice--registry-module
# @FileName: views.py
# @Software: PyCharm
"""
from starlette.requests import Request
from starlette.responses import JSONResponse, RedirectResponse

from .schemas import schemas
from starlette_utils.response import api_endpoints


async def swagger_view(request: Request, *args, **kwargs):
    return RedirectResponse(url='/static/swagger/index.html')


class OpenApi(api_endpoints.RetrieveApiView):
    routes = []

    @classmethod
    def get_schemas(cls, routes):
        cls.routes = routes
        return OpenApi

    def get(self, request, *args, **kwargs):
        return JSONResponse(schemas.get_schema(self.routes))
