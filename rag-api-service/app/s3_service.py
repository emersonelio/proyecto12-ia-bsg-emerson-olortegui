import os
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

    def download_folder(self, s3_prefix, local_folder):
        os.makedirs(local_folder, exist_ok=True)

        response = self.s3.list_objects_v2(
            Bucket=self.bucket_name,
            Prefix=s3_prefix.rstrip("/") + "/"
        )

        for obj in response.get("Contents", []):
            key = obj["Key"]

            if key.endswith("/"):
                continue

            relative_path = key.replace(
                s3_prefix.rstrip("/") + "/",
                ""
            )

            local_path = os.path.join(
                local_folder,
                relative_path
            )

            os.makedirs(
                os.path.dirname(local_path),
                exist_ok=True
            )

            print(
                f"Descargando s3://{self.bucket_name}/{key} -> {local_path}"
            )

            self.s3.download_file(
                self.bucket_name,
                key,
                local_path
            )