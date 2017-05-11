# -*- coding: utf-8 -*-
from django.conf import settings
from django.conf.urls import url
from sherlockwaste.settings import SENDFILE_URL

from og_django_utils.secure_media import secure_download_view, secure_download_view_encrypted

urlpatterns = []

if getattr(settings, 'ENCRYPT_PRIVATE_MEDIA_PARAMS', False):
    urlpatterns.append(
        url(r'^{}(?:(?P<variant>\w+)/)?$'.format(SENDFILE_URL[1:]), secure_download_view_encrypted, name='secure-download')
    )
else:
    urlpatterns.append(
        url(r'^{}(?P<app_name>\w+)/(?P<model_name>\w+)/(?P<instance_id>\d+)/(?P<field_name>.+?)/(?:(?P<variant>\w+)/)?$'.format(SENDFILE_URL[1:]),
            secure_download_view, name='secure-download')
    )
