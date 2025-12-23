import pytest
from django.core.exceptions import ValidationError

from og_django_utils.utils.validators import OneNumericAndUppercaseValidator


class TestOneNumericAndUppercaseValidator:
    """Test password validator for Django 4.x compatibility"""

    def setup_method(self):
        self.validator = OneNumericAndUppercaseValidator()

    def test_valid_password(self):
        """Test that valid passwords pass validation"""
        valid_passwords = [
            "Password1",
            "Test123",
            "MyP@ssw0rd",
            "Abc123def",
        ]
        for password in valid_passwords:
            self.validator.validate(password)

    def test_missing_digit(self):
        """Test that password without digit raises ValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            self.validator.validate("PasswordOnly")
        assert "digit" in str(exc_info.value).lower()

    def test_missing_lowercase(self):
        """Test that password without lowercase raises ValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            self.validator.validate("PASSWORD123")
        assert "lowercase" in str(exc_info.value).lower()

    def test_missing_uppercase(self):
        """Test that password without uppercase raises ValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            self.validator.validate("password123")
        assert "uppercase" in str(exc_info.value).lower()

    def test_get_help_text(self):
        """Test that help text is returned"""
        help_text = self.validator.get_help_text()
        assert help_text is not None
        assert isinstance(help_text, str)
        assert len(help_text) > 0
