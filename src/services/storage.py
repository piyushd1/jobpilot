import os
import boto3
from botocore.exceptions import ClientError
from cryptography.fernet import Fernet
import io

class MinioStorage:
    def __init__(self):
        self.endpoint_url = os.getenv("MINIO_ENDPOINT_URL", "http://localhost:9000")
        self.access_key = os.getenv("MINIO_ACCESS_KEY", "admin")
        self.secret_key = os.getenv("MINIO_SECRET_KEY", "password123")
        self.bucket_name = "jobpilot-resumes"
        
        # In a real setup, this would be fetched from Vault or secure env
        # Key must be 32 url-safe base64-encoded bytes
        key = os.getenv("ENCRYPTION_KEY", Fernet.generate_key().decode('utf-8'))
        self.cipher_suite = Fernet(key.encode('utf-8'))

        self.s3_client = boto3.client(
            's3',
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key
        )

    def upload_file(self, file_content: bytes, object_name: str) -> str:
        """Encrypts and uploads a file to MinIO, returns the object path."""
        try:
            encrypted_content = self.cipher_suite.encrypt(file_content)
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=object_name,
                Body=encrypted_content
            )
            return f"s3://{self.bucket_name}/{object_name}"
        except ClientError as e:
            # Add logging here
            raise Exception(f"Failed to upload file to MinIO: {e}")

    def get_signed_url(self, object_name: str, expiration: int = 3600) -> str:
        """Returns a presigned URL to download the file."""
        try:
            response = self.s3_client.generate_presigned_url('get_object',
                                                    Params={'Bucket': self.bucket_name,
                                                            'Key': object_name},
                                                    ExpiresIn=expiration)
            return response
        except ClientError as e:
            raise Exception(f"Failed to generate presigned URL: {e}")

    def delete_file(self, object_name: str) -> bool:
        """Deletes a file from MinIO."""
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=object_name)
            return True
        except ClientError as e:
            raise Exception(f"Failed to delete file from MinIO: {e}")

    def download_and_decrypt(self, object_name: str) -> bytes:
        """Downloads a file and decrypts its contents."""
        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=object_name)
            encrypted_data = response['Body'].read()
            return self.cipher_suite.decrypt(encrypted_data)
        except ClientError as e:
            raise Exception(f"Failed to download or decrypt file: {e}")
