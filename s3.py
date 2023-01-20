import os
import time
import boto3
from dotenv import load_dotenv
load_dotenv()


VOLATILITY_METADATA_BUCKET_NAME = os.environ.get('VOLATILITY_METADATA_BUCKET_NAME')
VOLATILITY_CACHE_BUCKET_NAME = os.environ.get('VOLATILITY_CACHE_BUCKET_NAME')
VOLATILITY_KEY = os.environ.get('VOLATILITY_KEY')
VOLATILITY_METADATA_KEY = os.environ.get('VOLATILITY_METADATA_KEY')
AWS_KEY_ID = os.environ.get('AWS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')

s3_client = boto3.client("s3",
                         region_name="us-west-2",
                         aws_access_key_id=AWS_KEY_ID,
                         aws_secret_access_key=AWS_SECRET_ACCESS_KEY)


def s3_get_volatility_metadata():
    return s3_client.get_object(Bucket=VOLATILITY_METADATA_BUCKET_NAME, Key=VOLATILITY_METADATA_KEY)[
        "Body"].read().decode("utf-8").strip()


def s3_update_metadata(body):
    err = ""
    for i in range(5):
        try:
            s3_client.put_object(Bucket=VOLATILITY_METADATA_BUCKET_NAME, Body=body, Key=VOLATILITY_METADATA_KEY)
            return
        except Exception as e:
            err = e
            time.sleep(1)
    if err != "":
        raise err


def s3_put_volatility(body):
    err = ""
    for i in range(5):
        try:
            s3_client.put_object(Bucket=VOLATILITY_CACHE_BUCKET_NAME, Body=body, Key=VOLATILITY_KEY)
            return
        except Exception as e:
            err = e
            time.sleep(1)
    if err != "":
        raise err
