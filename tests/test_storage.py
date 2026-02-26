import pytest
from django.core.files.storage import FileSystemStorage

from og_django_utils.utils.storage import get_storage_class


def test_get_storage_class_with_alias():
    """Test getting storage class from alias like 'default'."""
    storage_class = get_storage_class("default")
    assert storage_class is not None
    assert callable(storage_class)


def test_get_storage_class_with_dotted_path():
    """Test getting storage class from dotted import path."""
    storage_class = get_storage_class("django.core.files.storage.FileSystemStorage")
    assert storage_class is FileSystemStorage


def test_get_storage_class_with_invalid_type():
    """Test that non-string input raises TypeError."""
    with pytest.raises(TypeError):
        get_storage_class(123)

    with pytest.raises(TypeError):
        get_storage_class(None)
