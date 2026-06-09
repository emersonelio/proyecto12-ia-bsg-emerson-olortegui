import os
import json
import boto3


class S3Service:

    def __init__(self):
        self.bucket_name = os.getenv("BUCKET_NAME") or os.getenv("S3_BUCKET")
        self.aws_region = os.getenv("AWS_REGION")

        if not self.bucket_name:
            raise ValueError("Falta configurar BUCKET_NAME o S3_BUCKET en el archivo .env")

        if not self.aws_region:
            raise ValueError("Falta configurar AWS_REGION en el archivo .env")

        self.s3 = boto3.client(
            "s3",
            region_name=self.aws_region
        )

    def list_chunk_files(self):
        response = self.s3.list_objects_v2(
            Bucket=self.bucket_name,
            Prefix="processed/chunks/"
        )

        files = []

        for obj in response.get("Contents", []):
            key = obj["Key"]

            if key.endswith("_chunks.json"):
                files.append(key)

        return files

    def download_json(self, key):
        response = self.s3.get_object(
            Bucket=self.bucket_name,
            Key=key
        )

        content = response["Body"].read().decode("utf-8")

        return json.loads(content)