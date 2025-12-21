from werkzeug.utils import secure_filename
import boto3
from botocore.client import Config as BotoConfig
from botocore.exceptions import ClientError
from flask import current_app
import uuid, mimetypes

def get_s3_client():
    cfg = current_app.config
    botocfg = BotoConfig(signature_version='s3v4', region_name=cfg.get('AWS_REGION'))
    return boto3.client(
        's3',
        region_name=cfg.get('AWS_REGION'),
        endpoint_url=cfg.get('S3_ENDPOINT'),
        aws_access_key_id=cfg.get('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=cfg.get('AWS_SECRET_ACCESS_KEY'),
        config=botocfg
    )

def make_s3_key(prefix, filename):
    name = secure_filename(filename)
    return f"{prefix}/{uuid.uuid4().hex}/{name}"

def upload_fileobj_to_s3(fileobj, bucket, key, content_type = None, public = False):
    client = get_s3_client()
    extra_args = {}
    if content_type:
        extra_args['ContentType'] = content_type
    if public:
        extra_args['ACL'] = 'public-read'
    try:
        client.upload_fileobj(fileobj, bucket, key , ExtraArgs=extra_args)
        return True
    except ClientError:
        current_app.logger.error("S3 upload failed: %s", ClientError)
        return False

def generate_s3_url(bucket, key, expires_in=3600, public=False):
    cfg = current_app.config
    client = get_s3_client()
    if public and cfg.get('S3_ENDPOINT'):
        return  f"{cfg.get('S3_ENDPOINT').rstrip('/')}/{bucket}/{key}"
    try:
        return client.generate_presigned_url('get_object', Params = {'Bucket': bucket, 'Key': key}, ExpiresIn=expires_in)
    except ClientError:
        current_app.logger.error("Presign failed: %s", ClientError)
        return None

def copy_object_s3(src_bucket, src_key, dst_bucket, dst_key):
    client = get_s3_client()
    try:
        copy_source = {'Bucket': src_bucket, 'Key': src_key}
        client.copy_object(Bucket=dst_bucket, CopySource=copy_source, Key=dst_key)
        return True
    except ClientError as e:
        current_app.logger.exception("S3 copy failed: %s", e)
        return False

def delete_object_s3(bucket, key):
    client = get_s3_client()
    try:
        client.delete_object(Bucket=bucket, Key=key)
        return True
    except ClientError as e:
        current_app.logger.exception("S3 delete failed: %s", e)
        return False

