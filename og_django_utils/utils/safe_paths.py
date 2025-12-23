# -*- coding: utf-8 -*-
import os
import six
from uuid import uuid4

from django.conf import settings
from django.utils.deconstruct import deconstructible
from django.utils.text import slugify


def normalize_polish_chars(text):
    if six.PY2:
        if type(text) is not six.text_type:
            text = six.text_type(text, 'utf-8')
    trans_tab = {u'ą': 'a', u'ć': 'c', u'ę': 'e', u'ł': 'l', u'ń': 'n', u'ó': 'o', u'ś': 's', u'ż': 'z', u'ź': 'z',
                 u'Ą': 'A', u'Ć': 'C', u'Ę': 'E', u'Ł': 'L', u'Ń': 'N', u'Ó': 'O', u'Ś': 'S', u'Ż': 'Z', u'Ź': 'Z'}
    return ''.join(trans_tab.get(char, char) for char in text)


def safe_ascii(text):
    text = normalize_polish_chars(text)
    text_safe = ""
    for char in text:
        if not ord(char) < 48 or ord(char) > 127:
            text_safe += char
    return slugify(text_safe)


# GOODTOKNOW: You can let Django serialize your own custom class instances by giving the class a deconstruct() method.
# It takes no arguments, and should return a tuple of three things (path, args, kwargs):

@deconstructible
class SafePath(object):
    def __init__(self, path, add_hash=True, hash_length=getattr(settings, 'FILE_RANDOM_HASH_LENGTH', 10)):
        self.path = path
        self.add_hash = add_hash
        self.hash_length = hash_length

    def __call__(self, instance, filename):
        if not callable(self.path):
            path = self.path
        else:
            path = os.path.dirname(self.path(instance, filename))
            filename = os.path.basename(self.path(instance, filename))

        filename, extension = os.path.splitext(filename)
        hash_value = ('_' + uuid4().hex[:self.hash_length]) if self.add_hash else ''
        new_filename = safe_ascii(filename + hash_value) + extension
        return os.path.join(path, new_filename)
