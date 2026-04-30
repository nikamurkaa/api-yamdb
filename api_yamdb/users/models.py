from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models

from .constants import (EMAIL_MAX_LENGTH, ROLE_MAX_LENGTH,
                        USERNAME_MAX_LENGTH)
from .validators import validate_username_not_reserved


class User(AbstractUser):
    """Кастомная модель пользователя."""

    class Role(models.TextChoices):
        USER = 'user', 'Пользователь'
        MODERATOR = 'moderator', 'Модератор'
        ADMIN = 'admin', 'Администратор'

    username = models.CharField(
        max_length=USERNAME_MAX_LENGTH,
        unique=True,
        validators=(UnicodeUsernameValidator(),
                    validate_username_not_reserved),
        error_messages={
            'unique': 'Пользователь с таким username уже существует.',
        },
        verbose_name='имя пользователя',
    )
    role = models.CharField(
        max_length=ROLE_MAX_LENGTH,
        choices=Role.choices,
        default=Role.USER,
        verbose_name='Роль',
    )
    bio = models.TextField(
        blank=True,
        verbose_name='биография',
    )
    email = models.EmailField(
        max_length=EMAIL_MAX_LENGTH,
        unique=True,
        verbose_name='электронная почта',
    )

    class Meta:
        ordering = ('id',)
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    @property
    def is_admin(self):
        return (
            self.role == self.Role.ADMIN
            or self.is_staff
            or self.is_superuser
        )

    @property
    def is_moderator(self):
        return (
            self.role == self.Role.MODERATOR
            or self.is_admin
            or self.is_superuser
        )

    def __str__(self):
        return self.username
