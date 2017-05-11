# -*- coding: utf-8 -*-
from django.db.models.fields.files import ImageFieldFile, FileField, FieldFile, ImageField
from stdimage.models import StdImageField, StdImageFieldFile


class SecureImageFileMixin(object):
    is_secure_media = True

    def _get_url(self):
        self._require_file()
        return self.storage.url(self.name, field_value=self)

    url = property(_get_url)

    def get_path(self, *args, **kwargs):
        return self.name


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
