import django
from packaging.version import Version

try:
    dj_version = Version(django.get_version())
except Exception:
    dj_version = Version("4.2")

# Django 1.7+ is required (we're on Django 4.2+)
default_app_config = "og_django_utils.custom_permissions.apps.CustomPermissions"
