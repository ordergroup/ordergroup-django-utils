from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


class OneNumericAndUppercaseValidator:
    """
    Validate whether the password has at least one number, one uppercase character and one lowercase character.
    """

    def validate(self, password, user=None):
        # check for digit
        if not any(char.isdigit() for char in password):
            raise ValidationError(_("Your password must contain at least one digit."))

        # check for a lowercase letter
        if not any(char.isalpha() and char.islower() for char in password):
            raise ValidationError(_("Your password must contain at least one lowercase letter."))

        # check for an uppercase letter
        if not any(char.isalpha() and char.isupper() for char in password):
            raise ValidationError(_("Your password must contain at least one uppercase letter."))

    def get_help_text(self):
        return _("Your password must contain at least one uppercase letter, one lowercase leter and one digit.")
