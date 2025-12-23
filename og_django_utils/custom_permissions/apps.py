from django.apps import AppConfig
from django.db.models.signals import post_migrate

from .loader import create_permissions


class CustomPermissions(AppConfig):
    name = 'og_django_utils.custom_permissions'
    verbose_name = "OG Django Custom Permissions"

    def ready(self):
        post_migrate.connect(create_permissions)
