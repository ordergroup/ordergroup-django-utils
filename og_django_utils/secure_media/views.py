# -*- coding: utf-8 -*-

from django.apps import apps
from django.conf import settings
from django.http.response import HttpResponseForbidden, HttpResponseNotFound
from sendfile import sendfile
from sherlockwaste.settings import SENDFILE_ROOT

from og_django_utils.secure_media import ParamEncryption


def secure_download_view(request, app_name, model_name, instance_id, field_name, variant=None):
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
    if not model_field or not getattr(model_field, 'is_secure_media', False):
        return HttpResponseForbidden()

    access_verification = getattr(model_instance, 'verify_private_media_access', None)
    if access_verification and callable(access_verification):
        try:
            allow_access = access_verification(request, field_name)
            if allow_access:
                file_path = SENDFILE_ROOT + model_field.get_path(variant=variant)
                return sendfile(request, file_path)
            else:
                return HttpResponseForbidden()
        except:
            raise
    raise NotImplementedError('verify_private_media_access method for secure media is not implemented in class {}.{}'.format(app_name, model_name))


def secure_download_view_encrypted(request, variant):
    enc_path = request.GET.get('p', None)
    if not enc_path:
        return HttpResponseNotFound()
    try:
        params = ParamEncryption(getattr(settings, 'PRIVATE_MEDIA_KEY', None)).decrypt_params(enc_path)
        params_list = params.split('/')
        if len(params_list) != 4:
            return HttpResponseForbidden()
        app_name, model_name, instance_id, field_name = params_list
        return secure_download_view(request, app_name, model_name, instance_id, field_name, variant)
    except Exception as e:
        return HttpResponseForbidden()
