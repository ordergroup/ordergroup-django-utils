from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.files.storage import FileSystemStorage

try:
    from urlparse import urljoin  # Python 2.X
except ImportError:
    from urllib.parse import urljoin  # Python 3+

from .utils import ParamEncryption


class SecureFileStorage(FileSystemStorage):
    def __init__(
        self,
        location=getattr(settings, "SENDFILE_ROOT", None),
        base_url=getattr(settings, "SECURE_MEDIA_URL", None),
        file_permissions_mode=None,
        directory_permissions_mode=None,
    ):
        super().__init__(location, base_url, file_permissions_mode, directory_permissions_mode)
        self.encrpt_urls = getattr(settings, "ENCRYPT_PRIVATE_MEDIA_PARAMS", False)
        if self.encrpt_urls:
            crypt_key = getattr(settings, "PRIVATE_MEDIA_KEY", None)
            if not crypt_key:
                raise ImproperlyConfigured(
                    "Private media encryption enabled and encryption key parameter PRIVATE_MEDIA_KEY not set"
                )
            self.crypt = ParamEncryption(crypt_key)
        else:
            self.crypt = None

    def url(self, name, field_value=None):
        if self.base_url is None:
            raise ValueError("This file is not accessible via a URL.")

        instance = field_value.instance
        url_path = f"{instance._meta.app_label}/{instance.__class__.__name__}/{instance.id}/{field_value.field.attname}"
        if self.encrpt_urls:
            url_path = self.crypt.encrypt_params(url_path)
            return self.base_url + "?p=" + url_path
        else:
            return urljoin(self.base_url, url_path)
