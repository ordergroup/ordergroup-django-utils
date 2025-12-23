try:
    from rest_framework.fields import Field

    class SecureFieldBase64SerializerField(Field):
        """
        Serializator zwracający zakodowaną zawartość base64 dla plików SecureMedia
        """

        def __init__(self, variant=None, no_filename=False, **kwargs):
            super().__init__(**kwargs)
            self.variant = variant
            self.no_filename = no_filename

        def to_representation(self, instance):
            return instance.get_b64_content(self.variant, self.no_filename)

except ImportError:
    raise ImportError("This feature requires the djangorestframework package to be installed")
