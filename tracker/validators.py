from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
import re


class CustomPasswordValidator:
    """
    ADHD-friendly password validation.
    Requirements: letters + numbers + 8 chars minimum.
    Removed common password check - too restrictive.
    """
    
    def validate(self, password, user=None):
        """Validate password has letters and numbers"""
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
        """What shows up on the form"""
        return "Your password must contain at least one letter and one number."


def validate_username(username):
    """
    Username rules - keeping it simple and clear.
    
    - Letters, numbers, underscores only
    - 3-30 characters
    - No weird special characters that might break things
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