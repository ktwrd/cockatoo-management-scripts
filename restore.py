from dotenv import load_dotenv
import db, const, argparse, boto3, os, subprocess, shutil
from os import path, mkdir, getenv
from util import envkey_exists

parser = argparse.ArgumentParser(
    prog='Cockatoo - Restore Tool',
    description='Restore an existing backup from S3')
parser.add_argument('-t', '--tag',
                    dest='tag',
                    action='store', 
                    required=True, 
                    help='Tag that was used to create the backup.')
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

def restore_database_backup(directory):
    print('[restore_database_backup] Connecting to server...')
    connection = const.get_mongo_client()
    if connection is None:
        print('[restore_database_backup] Could not get client, since const.get_mongo_client() returned None')
        return False
    dbname = const.get_mongo_database_name()
    if dbname is None or len(dbname) < 1:
        print('[restore_database_backup] Missing required environment variable (%s)' % const.env_mongo_database())
        return False
    print('[restore_database_backup] Restoring backup')
    db.restore(directory, connection, dbname)

def s3_download(local_file, remote_location):
    client = boto3.client(
        service_name = 's3', 
        endpoint_url = getenv(const.env_ipo_s3_endpoint_url()),
        aws_access_key_id = getenv(const.env_ipo_s3_access_key()),
        aws_secret_access_key = getenv(const.env_ipo_s3_access_secret()),
        region_name = 'auto')
    client.download_file(const.get_ipo_s3_bucket_backup(), remote_location, local_file)
    print('[s3_download] Downloaded %s' % remote_location)
    
def decompress_backup(directory, file):
    print('[decomress_backup] Decompressing %s to %s' % (file, directory))
    if path.exists(directory):
        shutil.rmtree(directory)
    mkdir(directory)
    script = 'cd \'%s\'; zip -o \'%s\'' % (directory, file)
    proc = subprocess.run(script, shell=True, check=True, capture_output=True)
    if proc.returncode != 0:
        print('[decompress_backup] Failed to decompress backup! (exited with code %s)' % proc.returncode)
        print('stdout: %s' % proc.stdout)
        print('stderr: %s' % proc.stderr)
        exit()

def logic():
    if check_dotenv() > 0:
        print('One or more errors occoured, please check your .env file!')
        exit()
    out_dir = path.join(const.get_ipo_directory_temp(), '%s/' % args.tag)
    out_zip = path.join(const.get_ipo_directory_temp(), '%s.zip' % args.tag)
    out_env = path.join(const.get_ipo_directory_temp(), '%s.env' % args.tag)
    if path.exists(out_zip):
        os.remove(out_zip)
    s3_download(out_zip, '%s/database.zip' % args.tag)
    s3_download(out_env, '%s/.env' % args.tag)
    decompress_backup(out_dir, out_zip)
    if not restore_database_backup(out_dir):
        print('Failed to run restore_database_backup')
        exit()

logic()
