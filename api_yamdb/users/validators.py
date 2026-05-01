from django.core.exceptions import ValidationError

from .constants import RESERVED_USERNAMES


def validate_username_not_reserved(username):
    """Проверка, что username не равен зарезервированным значениям."""
    normalized_username = username.lower()

    if username.lower() in RESERVED_USERNAMES:
        error_text = f'Username {normalized_username} запрещён.'
        raise ValidationError(error_text)
    return username
