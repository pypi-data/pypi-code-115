# -*- encoding: utf-8 -*-
# @Author: haogooder
# @Date:
# @Description:
import gzip
import json
from functools import wraps

from flask import Response, request
from loguru import logger

# 默认多大执行压缩
COMPRESS_THRESHOLD = 256000
# 默认限制50M解压
LIMIT_REQUEST_DECOMPRESS_SIZE = 50000000
FAIL_RETURN = json.dumps({"code": 1001, "message": "params wrong", "data": {}})
INTERNAL_ERROR = json.dumps({"code": 1000, "message": "compress failed", "data": {}})
# 解压分片长度 （影响限制解压大小的情况）
DECOMPRESS_CHUNK_SIZE = 40960


def gzip_compress(source):
    """
    compress string, default using gzip algorithm
    :param source:
    :return:
    """
    if isinstance(source, str):
        source = source.encode("utf-8")
    return gzip.compress(source)


def gzip_decompress(source):
    """
    decompress string, default using gzip algorithm
    :param source:
    :return:
    """
    return gzip.decompress(source).decode('utf8')


def response_compress(threshold=COMPRESS_THRESHOLD):
    """
    对返回的数据做自动压缩
    :return:
    """

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(*args, **kwargs):
            response = view_func(*args, **kwargs)

            # 较小的包不压缩
            if isinstance(response, str) and len(response) < threshold:
                return response
            if isinstance(response, Response) and len(response.data) < threshold:
                return response

            # 压缩返回
            try:
                if isinstance(response, Response):
                    response_obj = response
                    response_obj.data = gzip_compress(response_obj.data)
                else:
                    response_obj = Response()
                    response_obj.data = gzip_compress(response)
                response_obj.headers['Content-Encoding'] = 'gzip'
                response_obj.headers['Content-Length'] = len(response_obj.data)
            except Exception as e:
                logger.exception(e)
                return INTERNAL_ERROR
            return response_obj

        return _wrapped_view

    return decorator


def auto_decompress():
    """
    接口自动处理解压情况
    :return:
    """

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(*args, **kwargs):
            content_encoding = request.headers.get('Content-Encoding', "")
            if content_encoding == "gzip":
                try:
                    decompress_data = gzip_decompress(request.data)

                    # 只设置了data， form，files等参数，后续看是否需要设置
                    setattr(request, "data", decompress_data)
                    # 由于缓存可能在之前已经被设置， 导致跟真实request.data不一致， 所以要同时设置缓存
                    # 对应版本： flask1.1.2，werkzeug1.0.1
                    # _cached_data是 werkzeug 设置的，_cached_json是 werkzeug 设置的
                    # werkzeug 1.0.1已经修改，不需要重新设置缓存
                    setattr(request, "_cached_data", decompress_data)
                except Exception as e:
                    logger.exception(e)
                    return FAIL_RETURN
            return view_func(*args, **kwargs)

        return _wrapped_view

    return decorator


if __name__ == "__main__":
    pass
