from base64 import b64encode

from django.apps import apps
from django.conf import settings
from django.http.response import HttpResponseForbidden, HttpResponseNotFound

try:
    from rest_framework.response import Response
    from rest_framework.views import APIView

    DRF_VIEWS = True
except ImportError:
    DRF_VIEWS = False

try:
    from sendfile import sendfile
except ImportError:
    raise ImportError("This feature requires the django-sendfile package to be installed")

from .utils import ParamEncryption

SENDFILE_ROOT = getattr(settings, "SENDFILE_ROOT", None)


def serve_file(request, file_path, base64):
    if base64:
        try:
            media_file = open(file_path, "rb")
            media_file_encoded = b64encode(media_file.read())
            return Response({"filename": file_path, "b64_data": media_file_encoded})
        except:
            return HttpResponseNotFound()
    return sendfile(request, file_path)


def get_media_file(request, app_name, model_name, instance_id, field_name, variant=None, base64=False):
    try:
        app_config = apps.get_app_config(app_name)
        model_class = app_config.get_model(model_name)
    except LookupError:
        return HttpResponseForbidden()
    try:
        model_instance = model_class.objects.get(pk=instance_id)
    except model_class.DoesNotExist:
        return HttpResponseNotFound()

    model_field = getattr(model_instance, field_name, None)
    if not model_field or not getattr(model_field, "is_secure_media", False):
        default_media_file = getattr(settings, "DEFAULT_SECURE_MEDIA_FILES", {}).get(
            f"{app_name}.{model_name}.{field_name}"
        )
        if default_media_file:
            if default_media_file[0] != "/":
                default_media_file = SENDFILE_ROOT + default_media_file
            return serve_file(request, default_media_file, base64)
        return HttpResponseNotFound()

    access_verification = getattr(model_instance, "verify_private_media_access", None)
    if access_verification and callable(access_verification):
        try:
            allow_access = access_verification(request, field_name)
            if allow_access:
                file_path = model_field.get_path(variant=variant)
                file_abs_path = SENDFILE_ROOT + file_path
                return serve_file(request, file_abs_path, base64)
            else:
                return HttpResponseForbidden()
        except:
            raise
    raise NotImplementedError(
        f"verify_private_media_access method for secure media is not implemented in class {app_name}.{model_name}"
    )


def get_media_file_base64(request, app_name, model_name, instance_id, field_name, variant=None):
    return get_media_file(request, app_name, model_name, instance_id, field_name, variant, base64=True)


def get_encrypted_media_file(request, variant, base64=False):
    enc_path = request.GET.get("p", None)
    if not enc_path:
        return HttpResponseNotFound()
    try:
        params = ParamEncryption(getattr(settings, "PRIVATE_MEDIA_KEY", None)).decrypt_params(enc_path)
        params_list = params.split("/")
        if len(params_list) != 4:
            return HttpResponseForbidden()
        app_name, model_name, instance_id, field_name = params_list
        return get_media_file(request, app_name, model_name, instance_id, field_name, variant, base64)
    except Exception:
        return HttpResponseForbidden()


def get_encrypted_media_file_base64(request, variant):
    return get_encrypted_media_file(request, variant, base64=True)


if DRF_VIEWS:

    class SecureDownloadView(APIView):
        def get(self, request, app_name, model_name, instance_id, field_name, variant=None):
            return get_media_file(request, app_name, model_name, instance_id, field_name, variant)

    class SecureDownloadViewBase64(APIView):
        def get(self, request, app_name, model_name, instance_id, field_name, variant=None):
            return get_media_file_base64(request, app_name, model_name, instance_id, field_name, variant)

    class SecureEncryptedDownloadView(SecureDownloadView):
        def get(self, request, variant):
            return get_encrypted_media_file(request, variant)

    class SecureEncryptedDownloadViewBase64(SecureDownloadView):
        def get(self, request, variant):
            return get_encrypted_media_file_base64(request, variant)

    secure_download_view = SecureDownloadView.as_view()
    secure_download_view_base64 = SecureDownloadViewBase64.as_view()
    secure_download_view_encrypted = SecureEncryptedDownloadView.as_view()
    secure_download_view_encrypted_base64 = SecureEncryptedDownloadViewBase64.as_view()

else:
    secure_download_view = get_media_file
    secure_download_view_base64 = get_media_file_base64
    secure_download_view_encrypted = get_encrypted_media_file
    secure_download_view_encrypted_base64 = get_encrypted_media_file_base64
