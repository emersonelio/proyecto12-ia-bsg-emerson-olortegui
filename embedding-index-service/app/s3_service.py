import os
import json
import boto3


class S3Service:

    def __init__(self):
        self.bucket_name = os.getenv("BUCKET_NAME") or os.getenv("S3_BUCKET")
        self.aws_region = os.getenv("AWS_REGION", "us-east-1")

        if not self.bucket_name:
            raise ValueError("Falta configurar BUCKET_NAME o S3_BUCKET")

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

    def upload_folder(self, local_folder, s3_prefix):
        for root, dirs, files in os.walk(local_folder):
            for file in files:
                local_path = os.path.join(root, file)

                relative_path = os.path.relpath(
                    local_path,
                    local_folder
                ).replace("\\", "/")

                s3_key = f"{s3_prefix.rstrip('/')}/{relative_path}"

                print(
                    f"Subiendo {local_path} -> "
                    f"s3://{self.bucket_name}/{s3_key}"
                )

                self.s3.upload_file(
                    local_path,
                    self.bucket_name,
                    s3_key
                )