from django.db import models
from django.test import TestCase

from og_django_utils.progressive_images.fields import ProgressiveImageField, ProgressiveImageFieldFile


class TestProgressiveImageField(TestCase):
    """Test ProgressiveImageField compatibility with Django 4.x"""

    def test_field_import(self):
        """Test that ProgressiveImageField can be imported"""
        assert ProgressiveImageField is not None

    def test_field_file_import(self):
        """Test that ProgressiveImageFieldFile can be imported"""
        assert ProgressiveImageFieldFile is not None

    def test_field_instantiation(self):
        """Test that ProgressiveImageField can be instantiated"""
        field = ProgressiveImageField(upload_to="test/", blank=True)
        assert field is not None
        assert field.upload_to == "test/"
        assert field.blank is True

    def test_field_with_variations(self):
        """Test that ProgressiveImageField works with variations"""
        variations = {
            "thumbnail": {"width": 100, "height": 100, "crop": True},
            "medium": {"width": 300, "height": 300},
        }
        field = ProgressiveImageField(upload_to="test/", variations=variations, blank=True)
        # Check that variations are set (django-stdimage adds defaults)
        assert "thumbnail" in field.variations
        assert "medium" in field.variations
        assert field.variations["thumbnail"]["width"] == 100
        assert field.variations["thumbnail"]["height"] == 100
        assert field.variations["medium"]["width"] == 300
        assert field.variations["medium"]["height"] == 300

    def test_field_deconstruct(self):
        """Test that field can be deconstructed for migrations"""
        field = ProgressiveImageField(upload_to="test/", blank=True)
        name, path, args, kwargs = field.deconstruct()
        assert path == "og_django_utils.progressive_images.fields.ProgressiveImageField"
        assert "upload_to" in kwargs
        assert kwargs["upload_to"] == "test/"


class TestModelWithProgressiveImageField(TestCase):
    """Test model integration with ProgressiveImageField"""

    def test_model_definition(self):
        """Test that a model can be defined with ProgressiveImageField"""

        class TestModel(models.Model):
            image = ProgressiveImageField(upload_to="test/", blank=True)

            class Meta:
                app_label = "tests"

        assert hasattr(TestModel, "image")
        field = TestModel._meta.get_field("image")
        assert isinstance(field, ProgressiveImageField)


def test_progressive_image_field_file_class():
    """Test ProgressiveImageFieldFile class attributes"""
    assert hasattr(ProgressiveImageFieldFile, "render_variation")
    assert callable(ProgressiveImageFieldFile.render_variation)
