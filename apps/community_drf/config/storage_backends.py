from urllib.parse import urljoin

from django.conf import settings
from storages.backends.s3 import S3Storage


class MinIOMediaStorage(S3Storage):
    bucket_name = settings.OBJECT_STORAGE_BUCKET_NAME
    access_key = settings.OBJECT_STORAGE_ACCESS_KEY_ID
    secret_key = settings.OBJECT_STORAGE_SECRET_ACCESS_KEY
    endpoint_url = settings.OBJECT_STORAGE_ENDPOINT_URL
    region_name = settings.OBJECT_STORAGE_REGION_NAME
    default_acl = None
    querystring_auth = False
    file_overwrite = True

    def url(self, name, parameters=None, expire=None, http_method=None):
        base_url = settings.OBJECT_STORAGE_PUBLIC_URL.rstrip("/") + "/"
        location = settings.OBJECT_STORAGE_LOCATION.strip("/")
        path = str(name).lstrip("/")

        if location:
            path = f"{location}/{path}"

        return urljoin(base_url, path)
