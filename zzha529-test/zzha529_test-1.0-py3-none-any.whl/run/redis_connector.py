import json
import redis


class RedisPool:
    def __init__(self):
        with open('./redis_config.json', 'r', encoding='utf8') as f:
            redis_json = json.load(f)
            self.port = redis_json["port"]
            self.host = redis_json["host"]

            self.pool = redis.ConnectionPool(host=self.host, port=self.port, decode_responses=True)

    def connector(self):
        return redis.Redis(connection_pool=self.pool, decode_responses=True)