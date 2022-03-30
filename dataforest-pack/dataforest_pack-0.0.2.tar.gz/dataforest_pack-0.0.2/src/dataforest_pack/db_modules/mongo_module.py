from pymongo import MongoClient


class MongoManager:
    def __init__(self, mongo_host, mongo_port=27017):
        self.mongo_host = mongo_host
        self.mongo_port = mongo_port
        self.mongo_client = self.__get_mongo_client()

    def __get_mongo_client(self):
        for _ in range(10):
            try:
                client = MongoClient(self.mongo_host, self.mongo_port)
                if client:
                    return client
            except:
                continue

        return None

    def insert_one_document_to_mongo(self, document, mongo_db, collection):
        my_collection = self.mongo_client[mongo_db][collection]
        document_id = my_collection.insert_one(document).inserted_id

        return document_id

    def insert_document_list_to_mongo(self, documents_list, mongo_db, collection):
        my_collection = self.mongo_client[mongo_db][collection]
        document_ids_list = my_collection.insert_many(documents_list).inserted_ids

        return document_ids_list
