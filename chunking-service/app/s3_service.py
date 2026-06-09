import os
import json
import boto3
from dotenv import load_dotenv

load_dotenv()

AWS_REGION = os.getenv("AWS_REGION")
S3_BUCKET = os.getenv("S3_BUCKET")

s3 = boto3.client(
    "s3",
    region_name=AWS_REGION
)


def list_metadata_files():
    response = s3.list_objects_v2(
        Bucket=S3_BUCKET,
        Prefix="processed/metadata/"
    )

    metadata_files = []

    for item in response.get("Contents", []):
        key = item["Key"]

        if key.lower().endswith(".json"):
            metadata_files.append(key)

    return metadata_files


def read_json(s3_key: str):
    response = s3.get_object(
        Bucket=S3_BUCKET,
        Key=s3_key
    )

    content = response["Body"].read().decode("utf-8")
    return json.loads(content)


def read_text(s3_key: str):
    response = s3.get_object(
        Bucket=S3_BUCKET,
        Key=s3_key
    )

    return response["Body"].read().decode("utf-8")


def upload_chunks(document_id: str, chunks):
    s3_key = f"processed/chunks/{document_id}_chunks.json"

    s3.put_object(
        Bucket=S3_BUCKET,
        Key=s3_key,
        Body=json.dumps(
            chunks,
            ensure_ascii=False,
            indent=2
        ).encode("utf-8")
    )

    return s3_key