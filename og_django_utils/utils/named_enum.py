from django.db import models


class En:
    counter = 0

    def __init__(self, verbose_name=None):
        self.verbose_name = verbose_name
        self.global_index = En.counter
        En.counter += 1


class NamedEnumMetaclass(type):
    def __new__(mcls, future_class_name, future_class_parents, future_class_attr):
        ens = mcls.extract_ens(future_class_attr)
        changed_future_class_attr = {k: v for k, v in future_class_attr.items() if not mcls.is_en(v)}
        names = {}
        mcls.prepare_ens_as_future_attr(ens, changed_future_class_attr, names)
        changed_future_class_attr["names"] = names
        changed_future_class_attr["choices"] = list(names.items())
        return type.__new__(mcls, future_class_name, future_class_parents, changed_future_class_attr)

    @classmethod
    def extract_ens(mcls, future_class_attr):
        ens = [(k, v) for k, v in future_class_attr.items() if mcls.is_en(v)]
        ens.sort(key=lambda kv: kv[1].global_index)
        return ens

    @classmethod
    def is_en(mcls, value):
        return isinstance(value, En)

    @classmethod
    def prepare_ens_as_future_attr(mcls, ens, changed_future_class_attr, names):
        index = 0
        for key, en in ens:
            name = en.verbose_name if en.verbose_name else key
            names[index] = name
            changed_future_class_attr[key] = index
            index += 1


class NamedEnum(metaclass=NamedEnumMetaclass):
    @classmethod
    def name(cls, option):
        return cls.names[option]

    @classmethod
    def named(cls, named):
        for k, v in cls.choices:
            if v == named:
                return k
        return None

    @classmethod
    def as_field(cls, default=None, **kwargs):
        return models.SmallIntegerField(default=default, choices=cls.choices, **kwargs)
