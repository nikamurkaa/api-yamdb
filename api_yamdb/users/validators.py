from django.core.exceptions import ValidationError

from .constants import RESERVED_USERNAMES


def validate_username_not_reserved(username):
    """Проверка, что username не равен зарезервированным значениям."""
    if (lowered_username := username.lower()) in RESERVED_USERNAMES:
        raise ValidationError(f'Username {lowered_username} запрещён.')
    return username
