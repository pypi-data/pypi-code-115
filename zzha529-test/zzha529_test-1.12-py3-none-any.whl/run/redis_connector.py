import json
import redis
import random


def singleton(cls, *args, **kw):
    instances = {}

    def _singleton():
        if cls not in instances:
            instances[cls] = cls(*args, **kw)
        return instances[cls]

    return _singleton


@singleton
class RedisPool(object):
    def __init__(self):
        with open(r'./redis_config.json', 'r', encoding='utf8') as f_load:
            redis_json = json.load(f_load)
        self.port = redis_json['port']
        self.host = redis_json['host']
        self.db = redis_json['db']
        self.random = random.random()
        self.pool = redis.ConnectionPool(host=self.host, port=self.port, db=self.db, decode_responses=True)

    def connector(self):
        return redis.Redis(connection_pool=self.pool, decode_responses=True)
