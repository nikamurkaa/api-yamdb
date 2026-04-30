from django.core.exceptions import ValidationError

RESERVED_USERNAME = 'me'


def validate_username_not_me(username):
    """Проверка, что username не равен зарезервированному значению 'me'."""

    if username.lower() == RESERVED_USERNAME:
        raise ValidationError('Username "me" запрещён.')
    return username
