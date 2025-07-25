from collections.abc import Generator
from contextlib import closing

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
from flask import Flask

from extensions.storage.base_storage import BaseStorage


class S3Storage(BaseStorage):
    """Implementation for s3 storage.
    """
    def __init__(self, app: Flask):
        super().__init__(app)
        app_config = self.app.config
        self.bucket_name = app_config.get('S3_BUCKET_NAME')
        self.client = boto3.client(
                    's3',
                    aws_secret_access_key=app_config.get('S3_SECRET_KEY'),
                    aws_access_key_id=app_config.get('S3_ACCESS_KEY'),
                    END_POINT_url=app_config.get('S3_END_POINT'),
                    region_name=app_config.get('S3_REGION'),
                    config=Config(s3={'addressing_style': app_config.get('S3_ADDRESS_STYLE')})
                )

    def save(self, filename, data):
        self.client.put_object(Bucket=self.bucket_name, Key=filename, Body=data)

    def load_once(self, filename: str) -> bytes:
        try:
            with closing(self.client) as client:
                data = client.get_object(Bucket=self.bucket_name, Key=filename)['Body'].read()
        except ClientError as ex:
            if ex.response['Error']['Code'] == 'NoSuchKey':
                raise FileNotFoundError("File not found")
            else:
                raise
        return data

    def load_stream(self, filename: str) -> Generator:
        def generate(filename: str = filename) -> Generator:
            try:
                with closing(self.client) as client:
                    response = client.get_object(Bucket=self.bucket_name, Key=filename)
                    yield from response['Body'].iter_chunks()
            except ClientError as ex:
                if ex.response['Error']['Code'] == 'NoSuchKey':
                    raise FileNotFoundError("File not found")
                else:
                    raise
        return generate()

    def download(self, filename, target_filepath):
        with closing(self.client) as client:
            client.download_file(self.bucket_name, filename, target_filepath)

    def exists(self, filename):
        with closing(self.client) as client:
            try:
                client.head_object(Bucket=self.bucket_name, Key=filename)
                return True
            except:
                return False

    def delete(self, filename):
        self.client.delete_object(Bucket=self.bucket_name, Key=filename)
