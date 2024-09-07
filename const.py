import bson, os
from util import envkey_exists
from pymongo import MongoClient

def env_mongo_connection():
    return 'MONGO_CONNECTION'
def get_mongo_client():
    if envkey_exists(env_mongo_connection()):
        return MongoClient(os.getenv(env_mongo_connection()))
    else:
        return None
def env_mongo_database():
    return 'MONGO_DATABASE'
def get_mongo_database_name():
    if envkey_exists(env_mongo_database()):
        return os.getenv(env_mongo_database())
    return None
def env_ipo_directory_tmp():
    return env_ipo_directory_temp()
def env_ipo_directory_temp():
    return '_IPO_DIRECTORY_TEMP'
def env_ipo_s3_access_key():
    return '_IPO_S3_ACCESS_KEY'
def env_ipo_s3_access_secret():
    return '_IPO_S3_ACCESS_SECRET'
def env_ipo_s3_endpoint_url():
    return '_IPO_S3_ENDPOINT_URL'
def env_ipo_s3_bucket_backup():
    return '_IPO_S3_BUCKET_BACKUP'
def get_ipo_s3_bucket_backup():
    if envkey_exists(env_ipo_s3_bucket_backup()):
        return os.getenv(env_ipo_s3_bucket_backup())
    return None
def get_ipo_directory_temp():
    value = os.path.abspath('./db-backup/')
    if envkey_exists(env_ipo_directory_temp()):
        value = os.path.abspath(os.getenv(env_ipo_directory_temp()))
    if not os.path.exists(value):
        os.makedirs(value, exist_ok=True)
    return value

        