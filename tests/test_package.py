import pytest
import og_django_utils


def test_package_version():
    """Test that package has a version"""
    assert hasattr(og_django_utils, '__version__')
    assert og_django_utils.__version__ == "0.2.0"


def test_package_import():
    """Test that package can be imported"""
    assert og_django_utils is not None


def test_django_compatibility():
    """Test Django 4.x compatibility"""
    import django
    django_version = tuple(map(int, django.__version__.split('.')[:2]))
    assert django_version >= (4, 2), f"Django version {django.__version__} is not 4.2+"


def test_stdimage_compatibility():
    """Test that django-stdimage is compatible"""
    from stdimage.models import StdImageField
    assert StdImageField is not None
