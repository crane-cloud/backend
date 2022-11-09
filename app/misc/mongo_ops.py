import os
from pymongo import MongoClient
from .append_time_details import append_time_details

client  = MongoClient(os.getenv("MONGO_HOST"))
mongo_db = os.getenv("MONGO_DATABASE")
database = client.mongo_db


def save_document(collection: str, data: dict, session=None):
    """
    - Add timestamp details for the data
    - Save the data to the database
    """
    data = append_time_details(data)
    if session is not None:
        database[collection].insert_one(data)
    else:
        database[collection].insert_one(data, session=session)


# collection strings
ACTION_LOG = "actionLogs"
