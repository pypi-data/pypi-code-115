from bson.json_util import dumps
from bson.json_util import loads
from transformHealthEventHubModels.utils import *


class DSEventHubUpdateOneObject(object):
    def __init__(self, collection, filter_condition, operation, upsert=False, array_filters=None, uniqueness_key_and=None, uniqueness_key_or=None):
        self.collection = collection
        self.filter_condition = filter_condition
        self.operation = operation
        self.upsert = upsert
        self.array_filters = array_filters
        self.uniqueness_key_and = uniqueness_key_and
        self.uniqueness_key_or = uniqueness_key_or

    def json(self):
        return {
            "collection": self.collection,
            "filter_condition": dumps(self.filter_condition),
            "operation": dumps(self.operation),
            "upsert": str(self.upsert),
            "array_filters": dumps(self.array_filters),
            "uniqueness_key_and": self.uniqueness_key_and,
            "uniqueness_key_or": self.uniqueness_key_or
        }

    @classmethod
    def load_object(cls, json_object):
        return cls(
            decodeUTFString(json_object[b"collection"]),
            loads(decodeUTFString(json_object[b"filter_condition"])),
            loads(decodeUTFString(json_object[b"operation"])),
            decodeUTFString(json_object[b"upsert"]) == "True",
            loads(decodeUTFString(json_object[b"array_filters"])),
            loads(decodeUTFString(json_object[b"uniqueness_key_and"])),
            loads(decodeUTFString(json_object[b"uniqueness_key_or"]))

        )
