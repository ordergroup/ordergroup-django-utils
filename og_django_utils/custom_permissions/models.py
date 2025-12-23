# -*- coding: utf-8 -*-
from django.conf import settings
from django.contrib.auth.models import Permission, PermissionManager
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import ugettext_lazy as _

APP_LABEL = getattr(settings, 'CUSTOM_PERMISSIONS_APP_LABEL', 'custom_permissions')


class CustomPermissionModel(models.Model):
    class Meta:
        managed = False
        default_permissions = ()
        verbose_name = _(u'Uprawnienie systemowe')
        verbose_name_plural = _(u'Uprawnienia systemowe')


class CustomPermissionManager(PermissionManager):
    def get_queryset(self):
        return super(CustomPermissionManager, self).get_queryset().filter(content_type=self.get_content_type())

    def get_content_type(self):
        ct, created = ContentType.objects.get_or_create(app_label=APP_LABEL, model="custompermissionmodel")
        return ct

    def create(self, **kwargs):
        if 'content_type' not in kwargs.keys():
            kwargs['content_type'] = self.get_content_type()
        return super(CustomPermissionManager, self).create(**kwargs)


class CustomPermission(Permission):
    objects = CustomPermissionManager()

    class Meta:
        proxy = True
        default_permissions = ()

    def save(self, *args, **kwargs):
        self.content_type = CustomPermission.objects.get_content_type()
        super(CustomPermission, self).save(*args, **kwargs)


class UserCustomPermissionMixin(object):
    def has_custom_perm(self, perm):
        if len(perm.split('.')) == 1 or not perm.startswith(APP_LABEL):
            perm = APP_LABEL + '.' + perm
            return self.has_perm(perm)

    def custom_permissions(self):
        return CustomPermission.objects.filter(user=self)
