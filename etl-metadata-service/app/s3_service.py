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


def list_pdf_files():
    response = s3.list_objects_v2(
        Bucket=S3_BUCKET,
        Prefix="raw/"
    )

    pdf_files = []

    for item in response.get("Contents", []):
        key = item["Key"]

        if key.lower().endswith(".pdf"):
            pdf_files.append(key)

    return pdf_files


def download_pdf(s3_key, local_path):
    s3.download_file(
        S3_BUCKET,
        s3_key,
        local_path
    )


def upload_text(file_name, text):
    s3_key = f"processed/text/{file_name}.txt"

    s3.put_object(
        Bucket=S3_BUCKET,
        Key=s3_key,
        Body=text.encode("utf-8")
    )

    return s3_key


def upload_metadata(file_name, metadata):
    s3_key = f"processed/metadata/{file_name}.json"

    metadata["s3_metadata_key"] = s3_key

    s3.put_object(
        Bucket=S3_BUCKET,
        Key=s3_key,
        Body=json.dumps(
            metadata,
            ensure_ascii=False,
            indent=2
        ).encode("utf-8")
    )

    return s3_key