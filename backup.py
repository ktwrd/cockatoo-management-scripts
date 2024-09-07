from dotenv import load_dotenv
import db, const, argparse, boto3, os, subprocess, shutil
from os import path, makedirs, getenv
from util import envkey_exists

parser = argparse.ArgumentParser(
    prog='Cockatoo - Backup Tool',
    description='Create and upload a database backup')
parser.add_argument('-t', '--tag',
                    dest='tag',
                    action='store', 
                    required=True, 
                    help='Tag for the backup, should be something memorable.')
parser.add_argument('-e', '--env-location',
                    dest='env_location',
                    action='store',
                    required=False,
                    default='.env.production',
                    help='Provide a different location to get the environment file from.')
args = parser.parse_args()

if args.tag is None:
    print('Argument \'--tag\' is required')
    exit()

load_dotenv(args.env_location)

def check_dotenv():
    error_count = 0
    error_template = '[check_dotenv] Missing environment variable %s'
    items = [
        const.env_mongo_connection(),
        const.env_mongo_database(),
        const.env_ipo_s3_bucket_backup(),
        const.env_ipo_s3_endpoint_url(),
        const.env_ipo_s3_access_key(),
        const.env_ipo_s3_access_secret()
    ]
    for key in items:
        if not envkey_exists(key):
            print(error_template % key)
            error_count += 1
    return error_count

def create_database_backup(tag):
    output_directory = path.join(const.get_ipo_directory_temp(), '%s' % tag)
    if path.exists(output_directory):
        shutil.rmtree(output_directory)
    makedirs(output_directory, exist_ok=True)
    print('[create_database_backup] Created directory %s' % output_directory)
    print('[create_database_backup] Connecting to server...')
    connection = const.get_mongo_client()
    if connection is None:
        print('[create_database_backup] Could not get client, since const.get_mongo_client() returned None')
        return False
    dbname = const.get_mongo_database_name()
    if dbname is None:
        print('[create_database_backup] Missing required environment variable (%s)' % const.env_mongo_database())
        return False
    collections = connection[dbname].list_collection_names()
    if len(collections) < 1:
        print('[create_database_backup] No collections found :3')
        shutil.rmtree(output_directory)
        exit()
    print('[create_database_backup] Fetching all collections (%s)' % len(collections))
    db.dump(collections, connection, dbname, output_directory)
    return output_directory

def s3_upload(local_file, target_location):
    client = boto3.client(
        service_name = 's3', 
        endpoint_url = getenv(const.env_ipo_s3_endpoint_url()),
        aws_access_key_id = getenv(const.env_ipo_s3_access_key()),
        aws_secret_access_key = getenv(const.env_ipo_s3_access_secret()),
        region_name = 'auto')
    client.upload_file(local_file, getenv(const.env_ipo_s3_bucket_backup()), target_location)
    print('[s3_upload] Uploaded %s' % target_location)
    
def compress_backup(directory, tag):
    target_zip_location = path.join(const.get_ipo_directory_temp(), '%s.zip' % tag)
    if path.exists(target_zip_location):
        os.remove(target_zip_location)
    script = 'cd \'%s\'; zip -r \'%s\' ./*' % (directory, target_zip_location)
    proc = subprocess.run(script, shell=True, check=True, capture_output=True)
    if proc.returncode != 0:
        print('[compress_backup] Failed to compress backup! (exited with code %s)' % proc.returncode)
        print('stdout: %s' % proc.stdout)
        print('stderr: %s' % proc.stderr)
        exit()
    return target_zip_location

def logic():
    if check_dotenv() > 0:
        print('One or more errors occoured, please check your .env file!')
        exit()
    backup_dir = create_database_backup(args.tag)
    dbzip = compress_backup(backup_dir, args.tag)
    s3_upload(dbzip, '%s/database.zip' % args.tag)
    s3_upload('./.env.production', '%s/.env' % args.tag)

logic()
