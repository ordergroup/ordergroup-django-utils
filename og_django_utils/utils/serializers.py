# -*- coding: utf-8 -*-

try:
    from rest_framework.fields import CharField

    class NamedEnumSerializerField(CharField):
        """
        Serializator mapujący wartości enuma na i z wartości tekstowych (API posługuje się stringami na zewnątrz)
        """
        def __init__(self, enum, **kwargs):
            super(NamedEnumSerializerField, self).__init__(**kwargs)
            self.enum = enum

        def to_representation(self, instance):
            return self.enum.name(instance)

        def to_internal_value(self, data):
            for value, name in self.enum.names.items():
                if name == data:
                    return value
            self.fail('invalid')


    class NamedEnumOptionsSerializerField(CharField):
        """
        Serializator dostępnych opcji dla danego enuma
        """
        def to_representation(self, instance):
            return instance.choices

except ImportError:
    pass