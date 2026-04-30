from django.core.exceptions import ValidationError
from django.utils import timezone


def validate_year_not_future(year):
    """Проверяет, что год произведения не больше текущего."""

    if year > timezone.now().year:
        raise ValidationError(
            'Год выпуска не может быть больше текущего.'
        )
