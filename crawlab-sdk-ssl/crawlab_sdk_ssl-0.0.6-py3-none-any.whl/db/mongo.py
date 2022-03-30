import os

from pymongo import MongoClient

from crawlab.utils.config import get_data_source


def get_col():
    ds = get_data_source()

    if ds.get("type") is None:
        # default data source
        mongo_host = os.environ.get("CRAWLAB_MONGO_HOST") or "localhost"
        mongo_port = int(os.environ.get("CRAWLAB_MONGO_PORT") or 27017) or 27017
        mongo_db = os.environ.get("CRAWLAB_MONGO_DB") or "test"
        mongo_username = os.environ.get("CRAWLAB_MONGO_USERNAME") or ""
        mongo_password = os.environ.get("CRAWLAB_MONGO_PASSWORD") or ""
        mongo_authsource = os.environ.get("CRAWLAB_MONGO_AUTHSOURCE") or "admin"
        collection = os.environ.get("CRAWLAB_COLLECTION") or "test"
        uri = f"mongodb://{mongo_username}:{mongo_password}@{mongo_host}:{mongo_port}/?ssl=true&retrywrites=false&replicaSet=globaldb&maxIdleTimeMS=120000"
        mongo = MongoClient(uri)
        db = mongo.get_database(mongo_db)
        col = db.get_collection(collection)

        return col

    # specified mongo data source
    uri = f"mongodb://{ds.get('username')}:{ds.get('password')}@{ds.get('host')}:{ds.get('port')}/?ssl=true&retrywrites=false&replicaSet=globaldb&maxIdleTimeMS=120000"
    mongo = MongoClient(uri)
    collection = os.environ.get("CRAWLAB_COLLECTION") or "test"
    db = mongo.get_database(ds.get("database"))
    col = db.get_collection(collection)
    return col
