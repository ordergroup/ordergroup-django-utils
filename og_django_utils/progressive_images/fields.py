
from stdimage.models import StdImageField, StdImageFieldFile


class ProgressiveImageFieldFile(StdImageFieldFile):
    # Tymczasowe obejście / placeholder

    @classmethod
    def render_variation(cls, file_name, *args, **kwargs):
        """Render an image variation and saves it to the storage."""
        try:
            return super().render_variation(file_name, *args, **kwargs)
        except OSError as e:
            print('Unable to generate variation for file {}, as it was not found'.format(file_name or kwargs.get('file_name')))


class ProgressiveImageField(StdImageField):
    attr_class = ProgressiveImageFieldFile

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
                    variation_field = ProgressiveImageFieldFile(instance, self, variation_name)
                    setattr(field, name, variation_field)
