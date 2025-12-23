import pytest
from django.db import models

from og_django_utils.utils.named_enum import NamedEnum, En


class TestNamedEnum:
    """Test NamedEnum functionality"""

    def test_basic_enum_creation(self):
        """Test creating a basic named enum"""
        
        class Status(NamedEnum):
            ACTIVE = En('Active')
            INACTIVE = En('Inactive')
            PENDING = En('Pending')
        
        assert Status.ACTIVE == 0
        assert Status.INACTIVE == 1
        assert Status.PENDING == 2

    def test_enum_names(self):
        """Test that enum names are correctly set"""
        
        class Status(NamedEnum):
            ACTIVE = En('Active')
            INACTIVE = En('Inactive')
            PENDING = En('Pending')
        
        assert Status.name(Status.ACTIVE) == 'Active'
        assert Status.name(Status.INACTIVE) == 'Inactive'
        assert Status.name(Status.PENDING) == 'Pending'

    def test_enum_choices(self):
        """Test that enum generates Django choices"""
        
        class Status(NamedEnum):
            ACTIVE = En('Active')
            INACTIVE = En('Inactive')
        
        assert hasattr(Status, 'choices')
        assert len(Status.choices) == 2
        assert (0, 'Active') in Status.choices
        assert (1, 'Inactive') in Status.choices

    def test_enum_named_lookup(self):
        """Test reverse lookup by name"""
        
        class Status(NamedEnum):
            ACTIVE = En('Active')
            INACTIVE = En('Inactive')
        
        assert Status.named('Active') == 0
        assert Status.named('Inactive') == 1
        assert Status.named('NonExistent') is None

    def test_enum_as_field(self):
        """Test creating Django model field from enum"""
        
        class Status(NamedEnum):
            ACTIVE = En('Active')
            INACTIVE = En('Inactive')
        
        field = Status.as_field(default=Status.ACTIVE, verbose_name='Status')
        assert isinstance(field, models.SmallIntegerField)
        assert field.default == Status.ACTIVE
        assert field.choices == Status.choices

    def test_enum_without_verbose_name(self):
        """Test enum without explicit verbose names uses attribute names"""
        
        class Priority(NamedEnum):
            HIGH = En()
            MEDIUM = En()
            LOW = En()
        
        assert Priority.name(Priority.HIGH) == 'HIGH'
        assert Priority.name(Priority.MEDIUM) == 'MEDIUM'
        assert Priority.name(Priority.LOW) == 'LOW'

    def test_enum_ordering(self):
        """Test that enum values maintain definition order"""
        
        class Level(NamedEnum):
            FIRST = En('First')
            SECOND = En('Second')
            THIRD = En('Third')
        
        assert Level.FIRST < Level.SECOND < Level.THIRD
        assert Level.choices[0] == (0, 'First')
        assert Level.choices[1] == (1, 'Second')
        assert Level.choices[2] == (2, 'Third')
