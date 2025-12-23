import six
from django.conf import settings
from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied
from django.utils.decorators import method_decorator

APP_LABEL = getattr(settings, "CUSTOM_PERMISSIONS_APP_LABEL", "custom_permissions")


def permission_required_extended(perm, login_url=None, raise_exception=False, raise_exception_for_users_only=False):
    """
    Modified default django mechanism that raises 403 only if the user is logged in
    """

    def check_perms(user):
        if isinstance(perm, six.string_types):
            perms = (perm,)
        else:
            perms = perm
        # First check if the user has the permission (even anon users)
        if user.has_perms(perms):
            return True
        # In case the 403 handler should be called raise the exception
        if raise_exception:
            is_authenticated = user.is_authenticated() if callable(user.is_authenticated) else user.is_authenticated
            if not raise_exception_for_users_only or is_authenticated:
                raise PermissionDenied
        # As the last resort, show the login form
        return False

    return user_passes_test(check_perms, login_url=login_url)


def require_custom_permission(perm_name, login_url=None, raise_exception=True, raise_exception_for_users_only=True):
    if len(perm_name.split(".")) == 1 or not perm_name.startswith(APP_LABEL):
        perm_name = APP_LABEL + "." + perm_name
    return permission_required_extended(perm_name, login_url, raise_exception, raise_exception_for_users_only)


def custom_permission_required(perm_name, login_url=None, raise_exception=True, raise_exception_for_users_only=True):
    decorator = require_custom_permission(perm_name, login_url, raise_exception, raise_exception_for_users_only)
    return method_decorator(decorator, name="dispatch")
