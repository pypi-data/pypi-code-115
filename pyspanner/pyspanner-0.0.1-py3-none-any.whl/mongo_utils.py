# -*- encoding: utf-8 -*-
# @Author: haogooder
# @Date:
# @Description:
from typing import Dict, List, Optional

from bson import ObjectId
from gridfs import GridFS, GridOut
from pymongo import MongoClient
from pymongo.collection import Collection, ReturnDocument

# mogndb socket超时时间（毫秒）
MONGO_SOCKET_TIMEOUT_MS = 300 * 1000


class MongoUtil(object):
    """
    MongoDB工具
    """

    def __init__(self, host: str, port: int = 27017,
                 user: str = None, password: str = None, auth_db: str = "admin", replicaset: str = None,
                 timeout_ms: int = MONGO_SOCKET_TIMEOUT_MS,
                 tls: bool = False, tls_allow_invalid_certificates: bool = False, tls_ca_file: str = "",
                 appname: str = None):
        if not isinstance(host, str) \
                or (not isinstance(user, str) and user is not None) \
                or (not isinstance(password, str) and password is not None) \
                or (not isinstance(auth_db, str) and auth_db is not None) \
                or (not isinstance(replicaset, str) and replicaset is not None):
            raise TypeError("MongoUtil参数类型非法")
        if host.strip() == "":
            raise ValueError("MongoUtil参数host不能为空")
        self.host = host
        self.port = port
        self.username = user
        self.password = password
        self.auth_db = auth_db
        self.replicaset = replicaset
        self.tls = tls
        self.tls_ca = tls_ca_file
        self.tls_allow_invalid_certificates = tls_allow_invalid_certificates
        self.appname = appname
        self.client = MongoClient(host=self.host, port=self.port, username=self.username, password=self.password,
                                  authSource=self.auth_db, replicaSet=self.replicaset,
                                  connect=False, connectTimeoutMS=20000, socketTimeoutMS=timeout_ms,
                                  maxPoolSize=100, minPoolSize=0, maxIdleTimeMS=None, maxConnecting=2,
                                  appname=self.appname)
        self.db = self.client[self.auth_db]

    def get_collection(self, collection_name: str) -> Collection:
        """
        获取mongo集群数据表
        :param collection_name: 集合名称
        :return:
        """
        return Collection(self.db, name=collection_name)

    def get_gridfs(self, collection_name: str) -> GridFS:
        """
        获取mongo集群文件数据表
        :param collection_name:
        :return:
        """
        return GridFS(self.db, collection=collection_name)

    @staticmethod
    def is_update_success(update_result, upsert=False, strict=False):
        """
        判断是否更新成功
        :param upsert:
        :param update_result:
        :param strict: 是否严格判断（非upsert模式下， 没匹配到是否算是失败）
        :return:
        """
        # upsert模式下， 既没有匹配到， 也没有插入， 则返回失败
        if upsert and update_result.matched_count == 0 and not update_result.upserted_id:
            return False
        # 非upsert模式下， 判定严格处理， 又没有匹配到， 则返回失败
        if not upsert and strict and update_result.matched_count == 0:
            return False
        return True

    def insert_one(self, collection_name: str, document: Dict) -> ObjectId:
        if not isinstance(collection_name, str) or not isinstance(document, Dict):
            raise TypeError()
        coll = self.get_collection(collection_name)
        result = coll.insert_one(document=document)
        return result.inserted_id

    def insert_many(self, collection_name: str, documents: List[Dict]) -> List[ObjectId]:
        if not isinstance(collection_name, str) or not isinstance(documents, List):
            raise TypeError()
        coll = self.get_collection(collection_name)
        result = coll.insert_many(documents=documents)
        return result.inserted_ids

    def find_one(self, collection_name: str, query_filter: Dict) -> Dict:
        if not isinstance(collection_name, str) or not isinstance(query_filter, Dict):
            raise TypeError()
        coll = self.get_collection(collection_name)
        result = coll.find_one(filter=query_filter)
        return result

    def find_many(self, collection_name: str, query_filter: Dict, skip=0, limit=0, sort=None) -> List[Dict]:
        if not isinstance(collection_name, str) or not isinstance(query_filter, Dict):
            raise TypeError()
        coll = self.get_collection(collection_name)
        result = coll.find(filter=query_filter, skip=skip, limit=limit, sort=sort)
        return [i for i in result]

    def count(self, collection_name: str, query_filter: Dict) -> int:
        if not isinstance(collection_name, str) or not isinstance(query_filter, Dict):
            raise TypeError()
        coll = self.get_collection(collection_name)
        result = coll.count_documents(filter=query_filter)
        return result

    def replace_one(self, collection_name: str, query_filter: Dict, new: Dict) -> int:
        if not isinstance(collection_name, str) \
                or not isinstance(query_filter, Dict) \
                or not isinstance(new, Dict):
            raise TypeError()
        coll = self.get_collection(collection_name)
        result = coll.replace_one(filter=query_filter, replacement=new)
        return result.modified_count

    def update_many(self, collection_name: str, query_filter: Dict, update_new: Dict) -> int:
        if not isinstance(collection_name, str) \
                or not isinstance(query_filter, Dict) \
                or not isinstance(update_new, Dict):
            raise TypeError()
        coll = self.get_collection(collection_name)
        result = coll.update_many(filter=query_filter, update=update_new)
        return result.modified_count

    def delete_one(self, collection_name: str, _id: str) -> int:
        if not isinstance(collection_name, str) or not isinstance(_id, str):
            raise TypeError()
        coll = self.get_collection(collection_name)
        result = coll.delete_one({"_id": ObjectId(_id)})
        return result.deleted_count

    def find_one_and_update(self, collection_name: str, _id: str, update_new: Dict) -> Optional[Dict]:
        if not isinstance(collection_name, str) \
                or not isinstance(_id, str) \
                or not isinstance(update_new, Dict):
            raise TypeError()
        coll = self.get_collection(collection_name)
        result = coll.find_one_and_update(filter={"_id": ObjectId(_id)}, update=update_new,
                                          return_document=ReturnDocument.BEFORE)
        return result

    def find_one_and_replace(self, collection_name: str, _id: str, new: Dict) -> Optional[Dict]:
        if not isinstance(collection_name, str) \
                or not isinstance(_id, str) \
                or not isinstance(new, Dict):
            raise TypeError()
        coll = self.get_collection(collection_name)
        result = coll.find_one_and_replace(filter={"_id": ObjectId(_id)}, replacement=new,
                                           return_document=ReturnDocument.BEFORE)
        return result

    def find_one_and_delete(self, collection_name: str, _id: str) -> Dict:
        if not isinstance(collection_name, str) or not isinstance(_id, str):
            raise TypeError()
        coll = self.get_collection(collection_name)
        result = coll.find_one_and_delete(filter={"_id": ObjectId(_id)})
        return result

    def save_binary(self, collection_name: str, data: bytes, filename: str = None, **kwargs) -> ObjectId:
        if not isinstance(collection_name, str) or not isinstance(data, bytes):
            raise TypeError()
        fs = self.get_gridfs(collection_name=collection_name)
        result = fs.put(data, filename=filename, **kwargs)
        return result

    def get_binary(self, collection_name: str, _id: str) -> bytes:
        if not isinstance(collection_name, str) or not isinstance(_id, str):
            raise TypeError()
        fs = self.get_gridfs(collection_name=collection_name)
        out = fs.get(file_id=ObjectId(_id))
        if not isinstance(out, GridOut):
            raise TypeError()
        with out:
            result = out.read()
        return result

    def delete_binary(self, collection_name: str, _id: str):
        if not isinstance(collection_name, str) or not isinstance(_id, str):
            raise TypeError()
        fs = self.get_gridfs(collection_name=collection_name)
        fs.delete(file_id=ObjectId(_id))

    def exists_binary(self, collection_name: str, _id: str) -> bool:
        if not isinstance(collection_name, str) or not isinstance(_id, str):
            raise TypeError()
        fs = self.get_gridfs(collection_name=collection_name)
        return fs.exists({"_id": ObjectId(_id)})

    def find_binary(self, collection_name: str, query_filter: Dict) -> List[GridOut]:
        if not isinstance(collection_name, str) or not isinstance(query_filter, Dict):
            raise TypeError()
        fs = self.get_gridfs(collection_name=collection_name)
        result = fs.find(query_filter)
        return [i for i in result]

    def list_binary(self, collection_name: str):
        if not isinstance(collection_name, str):
            raise TypeError()
        fs = self.get_gridfs(collection_name=collection_name)
        result = fs.list()
        return [i for i in result]
