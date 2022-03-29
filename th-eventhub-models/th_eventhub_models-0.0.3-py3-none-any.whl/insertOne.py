from bson.json_util import dumps
from bson.json_util import loads

from transformHealthEventHubModels.utils import *


class DSEventHubInsertOneObject(object):
    def __init__(self, collection, data, uniqueness_key_and=None, uniqueness_key_or=None):
        self.collection = collection
        self.data = data,
        self.uniqueness_key_and = uniqueness_key_and
        self.uniqueness_key_or = uniqueness_key_or

    def json(self):
        return {
            "collection": self.collection,
            "data": dumps(self.data, sort_keys=True, default=str),
            "uniqueness_key_and": self.uniqueness_key_and,
            "uniqueness_key_or": self.uniqueness_key_or
        }

    @classmethod
    def load_object(cls, json_data):
        data = decodeUTFString(json_data[b'data'])
        return cls(
            decodeUTFString(json_data[b'collection']),
            loads(data),
            decodeUTFString(json_data[b'uniqueness_key_and']),
            decodeUTFString(json_data[b'uniqueness_key_or'])
        )
