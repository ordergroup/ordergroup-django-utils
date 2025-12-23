import inspect
from importlib import import_module
from pydoc import locate

from django.apps import apps
from django.conf import settings


def get_app_name(app_name):
    type_ = locate(app_name)
    if inspect.isclass(type_):
        return type_.name
    return app_name


def create_permissions(**kwargs):
    permissions_list = []
    custom_permissions_module = getattr(settings, "CUSTOM_PERMISSIONS_MODULE", None)
    if custom_permissions_module:
        module = import_module(settings.custom_permissions_module)
        permissions_list += getattr(module, "CUSTOM_PERMISSIONS", [])

    for app_name in settings.INSTALLED_APPS:
        if app_name != "custom_permissions":
            app_name = get_app_name(app_name)
            try:
                module = import_module(".permissions", app_name)
                permissions_list += getattr(module, "CUSTOM_PERMISSIONS", [])
            except ImportError:
                pass

    app_config = apps.get_app_config("custom_permissions")
    CustomPermission = app_config.get_model("CustomPermission")
    for permission_codename, permision_name in permissions_list:
        CustomPermission.objects.get_or_create(codename=permission_codename, name=permision_name)
