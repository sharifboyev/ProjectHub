import uuid

import aioboto3
from botocore.exceptions import ClientError
from fastapi import UploadFile

from app.shared.config.settings import settings


class S3Client:
    def __init__(self):
        self.session = aioboto3.Session()
        self.config = {
            "aws_access_key_id": settings.S3_ACCESS_KEY,
            "aws_secret_access_key": settings.S3_SECRET_KEY,
            "endpoint_url": settings.S3_ENDPOINT_URL,
            "region_name": settings.S3_REGION,
        }
        self.bucket_name = settings.S3_BUCKET_NAME

    async def _get_client(self):
        return self.session.client("s3", **self.config)

    async def ensure_bucket_exists(self) -> None:
        """Создает бакет, если он еще не существует в MinIO/S3."""
        async with await self._get_client() as client:
            try:
                await client.head_bucket(Bucket=self.bucket_name)
            except ClientError:
                await client.create_bucket(Bucket=self.bucket_name)

    async def get_project_total_size(self, project_id: uuid.UUID | str | int) -> int:
        """Подсчитывает суммарный объем (в байтах) всех файлов проекта."""
        prefix = f"projects/{project_id}/"
        total_size = 0

        async with await self._get_client() as client:
            paginator = client.get_paginator("list_objects_v2")
            async for page in paginator.paginate(Bucket=self.bucket_name, Prefix=prefix):
                for obj in page.get("Contents", []):
                    total_size += obj.get("Size", 0)

        return total_size

    async def upload_file(self, file: UploadFile, s3_path: str) -> str:
        """Загружает файл в S3 и возвращает ключ объекта."""
        async with await self._get_client() as client:
            await client.upload_fileobj(
                file.file,
                self.bucket_name,
                s3_path,
                ExtraArgs={"ContentType": file.content_type},
            )
        return s3_path

    async def download_file(self, s3_path: str) -> bytes:
        """Скачивает файл из S3 в виде байтов."""
        async with await self._get_client() as client:
            response = await client.get_object(Bucket=self.bucket_name, Key=s3_path)
            async with response["Body"] as stream:
                return await stream.read()

    async def delete_file(self, s3_path: str) -> None:
        """Удаляет файл из S3."""
        async with await self._get_client() as client:
            await client.delete_object(Bucket=self.bucket_name, Key=s3_path)

    async def generate_presigned_url(
            self, file_key: str, expires_in: int = 3600
    ) -> str:
        """Генерирует ссылку для прямого скачивания файла из S3.

        :param file_key: Путь к файлу в bucket
        :param expires_in: Время жизни ссылки в секундах (по умолчанию 1 час)
        """
        async with await self._get_client() as client:
            try:
                url = await client.generate_presigned_url(
                    ClientMethod="get_object",
                    Params={
                        "Bucket": self.bucket_name,
                        "Key": file_key,
                    },
                    ExpiresIn=expires_in,
                )
                return url
            except ClientError as e:
                raise e

s3_client = S3Client()
