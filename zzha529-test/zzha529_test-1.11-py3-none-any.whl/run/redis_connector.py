import json
import redis


class RedisPool:
    def __init__(self):
        self.port = 6379
        self.host = "localhost"
        self.pool = redis.ConnectionPool(host=self.host, port=self.port, decode_responses=True)

    def connector(self):
        return redis.Redis(connection_pool=self.pool, decode_responses=True)