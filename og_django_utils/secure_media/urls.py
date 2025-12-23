# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function

from django.conf import settings
from django.conf.urls import url

from .views import secure_download_view, secure_download_view_encrypted, secure_download_view_encrypted_base64, secure_download_view_base64

urlpatterns = []

SECURE_MEDIA_URL = getattr(settings, 'SECURE_MEDIA_URL', '/private/')

if getattr(settings, 'ENCRYPT_PRIVATE_MEDIA_PARAMS', False):
    urlpatterns += [
        url(r'^{}b/(?:(?P<variant>\w+)/)?$'.format(SECURE_MEDIA_URL[1:]), secure_download_view_encrypted_base64, name='secure-download-base64'),
        url(r'^{}(?:(?P<variant>\w+)/)?$'.format(SECURE_MEDIA_URL[1:]), secure_download_view_encrypted, name='secure-download'),
    ]
else:
    urlpatterns += [
        url(r'^{}(?P<app_name>\w+)/(?P<model_name>\w+)/(?P<instance_id>\d+)/(?P<field_name>.+?)/b/(?:(?P<variant>\w+)/)?$'.format(
            SECURE_MEDIA_URL[1:]), secure_download_view_base64, name='secure-download-base64'),
        url(r'^{}(?P<app_name>\w+)/(?P<model_name>\w+)/(?P<instance_id>\d+)/(?P<field_name>.+?)/(?:(?P<variant>\w+)/)?$'.format(
            SECURE_MEDIA_URL[1:]), secure_download_view, name='secure-download')
    ]
