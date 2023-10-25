import re
from django.core.exceptions import ValidationError

def validate_password_not_entirely_numeric(new_password):
    if re.match(r'^\d+$', new_password):
        raise ValidationError("Password cannot be entirely numeric.")