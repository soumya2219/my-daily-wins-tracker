from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
import re


class CustomPasswordValidator:
    """
    Custom password validator requiring at least one number and one letter.
    """
    def validate(self, password, user=None):
        if not re.search(r'[0-9]', password):
            raise ValidationError(
                "Password must contain at least one number (0-9).",
                code='password_no_number',
            )
        if not re.search(r'[a-zA-Z]', password):
            raise ValidationError(
                "Password must contain at least one letter (a-z or A-Z).",
                code='password_no_letter',
            )

    def get_help_text(self):
        return "Your password must contain at least one letter and one number."


def validate_username(username):
    """
    Validate username contains only letters, numbers, and underscores.
    """
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        raise ValidationError(
            "Username can only contain letters, numbers, and underscores (_).",
            code='invalid_username',
        )
    if len(username) < 3:
        raise ValidationError(
            "Username must be at least 3 characters long.",
            code='username_too_short',
        )
    if len(username) > 30:
        raise ValidationError(
            "Username cannot be longer than 30 characters.",
            code='username_too_long',
        )