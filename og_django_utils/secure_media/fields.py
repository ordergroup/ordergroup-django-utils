# -*- coding: utf-8 -*-
from base64 import b64encode

from django.conf import settings
from django.db.models.fields.files import ImageFieldFile, FileField, FieldFile, ImageField
from stdimage.models import StdImageField, StdImageFieldFile


SENDFILE_ROOT = getattr(settings, 'SENDFILE_ROOT', None)


class SecureImageFileMixin(object):
    is_secure_media = True

    def _get_url(self):
        if not getattr(settings, 'DEFAULT_SECURE_MEDIA_FILES', {}).get(str(self.field)):
            self._require_file()
        return self.storage.url(self.name, field_value=self)

    url = property(_get_url)

    def get_path(self, *args, **kwargs):
        return self.name

    def get_b64_content(self, variant=None, no_filename=False):
        file_path = self.get_path(variant=variant)
        file_abs_path = SENDFILE_ROOT + file_path
        try:
            secure_file = open(file_abs_path, 'rb')
            secure_file_encoded = b64encode(secure_file.read())
        except:
            secure_file_encoded = ''
        secure_file_encoded = secure_file_encoded or ''
        if no_filename:
            return secure_file_encoded
        return {'filename': file_path, 'b64_data': secure_file_encoded}


class SecureFieldFile(SecureImageFileMixin, FieldFile):
    pass


class SecureImageFieldFile(SecureImageFileMixin, ImageFieldFile):
    pass


class SecureStdImageFieldFile(SecureImageFileMixin, StdImageFieldFile):
    def get_path(self, variant, *args, **kwargs):
        image = self
        if variant:
            image = getattr(self, variant, self)
        return image.name


class SecureFileField(FileField):
    attr_class = SecureFieldFile


class SecureImageField(ImageField):
    attr_class = SecureImageFieldFile


class SecureStdImageField(StdImageField):
    attr_class = SecureStdImageFieldFile

    def set_variations(self, instance=None, **kwargs):
        """
        Create a "variation" object as attribute of the ImageField instance.

        Variation attribute will be of the same class as the original image, so
        "path", "url"... properties can be used

        :param instance: FileField
        """
        if getattr(instance, self.name):
            field = getattr(instance, self.name)
            if field._committed:
                for name, variation in list(self.variations.items()):
                    variation_name = self.attr_class.get_variation_name(
                        field.name,
                        variation['name']
                    )
                    variation_field = SecureImageFieldFile(instance, self, variation_name)
                    setattr(field, name, variation_field)
