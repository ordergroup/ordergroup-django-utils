# -*- coding: utf-8 -*-
import django
from distutils.version import StrictVersion

try:
    dj_version = StrictVersion(django.get_version())
except:
    dj_version = StrictVersion('1.10')

if dj_version < StrictVersion('1.7'):
    from custom_permissions.loader import create_permissions
    create_permissions()
else:
    default_app_config = 'og_django_utils.custom_permissions.apps.CustomPermissions'
