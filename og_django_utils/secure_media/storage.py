# -*- coding: utf-8 -*-
from urlparse import urljoin

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.files.storage import FileSystemStorage
from sherlockwaste.settings import SENDFILE_ROOT, SENDFILE_URL

from og_django_utils.secure_media import ParamEncryption


class SecureFileStorage(FileSystemStorage):
    def __init__(self, location=SENDFILE_ROOT, base_url=SENDFILE_URL, file_permissions_mode=None, directory_permissions_mode=None):
        super(SecureFileStorage, self).__init__(location, base_url, file_permissions_mode, directory_permissions_mode)
        self.encrpt_urls = getattr(settings, 'ENCRYPT_PRIVATE_MEDIA_PARAMS', False)
        if self.encrpt_urls:
            crypt_key = getattr(settings, 'PRIVATE_MEDIA_KEY', None)
            if not crypt_key:
                raise ImproperlyConfigured('Private media encryption enabled and encryption key parameter ENCRYPT_PRIVATE_MEDIA_KEY not set')
            self.crypt = ParamEncryption(crypt_key)
        else:
            self.crypt = None

    def url(self, name, field_value=None):
        if self.base_url is None:
            raise ValueError("This file is not accessible via a URL.")

        instance = field_value.instance
        url_path = '{}/{}/{}/{}'.format(instance._meta.app_label, instance.__class__.__name__, instance.id, field_value.field.attname)
        if self.encrpt_urls:
            url_path = self.crypt.encrypt_params(url_path)
            return self.base_url + '?p=' + url_path
        else:
            return urljoin(self.base_url, url_path)
