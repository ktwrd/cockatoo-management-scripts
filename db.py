import bson, os
from pymongo import MongoClient
from dotenv import load_dotenv

def action():
    db_backup_dir = os.path.join(os.getcwd(), 'backups')
    conn_addr = os.environ.get('MONGO_CONNECTION', '')
    db_name = os.environ.get('MONGO_DATABASE', '')
    error_count = 0
    if conn_addr is None or len(conn_addr) < 1:
        print('Environment Variable MONGO_CONNECTION is required!')
        error_count += 1
    if db_name is None or len(db_name) < 1:
        print('Environment Variable MONGO_DATABASE is required!')
        error_count += 1
    if error_count > 0:
        print('One or more errors occoured.')
        exit()
        
    conn = MongoClient(conn_addr)
    collections = conn[db_name].list_collection_names()
    dump(collections, conn, db_name, db_backup_dir)

def dump(collections, conn, db_name, path):
    """
    MongoDB Dump
    :param collections: Database collections name
    :param conn: MongoDB client connection
    :param db_name: Database name
    :param path:
    :return:

    >>> DB_BACKUP_DIR = '/path/backups/'
    >>> conn = MongoClient("mongodb://admin:admin@127.0.0.1:27017", authSource="admin")
    >>> db_name = 'my_db'
    >>> collections = ['collection_name', 'collection_name1', 'collection_name2']
    >>> dump(collections, conn, db_name, DB_BACKUP_DIR)
    """

    db = conn[db_name]
    for coll in collections:
        with open(os.path.join(path, f'{coll}.bson'), 'wb+') as f:
            for doc in db[coll].find():
                f.write(bson.BSON.encode(doc))


def restore(path, conn, db_name):
    """
    MongoDB Restore
    :param path: Database dumped path
    :param conn: MongoDB client connection
    :param db_name: Database name
    :return:

    >>> DB_BACKUP_DIR = '/path/backups/'
    >>> conn = MongoClient("mongodb://admin:admin@127.0.0.1:27017", authSource="admin")
    >>> db_name = 'my_db'
    >>> restore(DB_BACKUP_DIR, conn, db_name)

    """

    db = conn[db_name]
    for coll in os.listdir(path):
        if coll.endswith('.bson'):
            with open(os.path.join(path, coll), 'rb+') as f:
                db[coll.split('.')[0]].insert_many(bson.decode_all(f.read()))