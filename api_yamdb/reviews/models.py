from django.core.validators import MaxValueValidator, MinValueValidator
from django.contrib.auth import get_user_model
from django.db import models

from .constants import (MAX_LENGTH_NAME, MAX_LENGTH_SLUG,
                        MIN_SCORE, MAX_SCORE, MAX_LENGTH_TEXT_STR)

from .validators import validate_year_not_future

User = get_user_model()


class Category(models.Model):
    name = models.CharField(max_length=MAX_LENGTH_NAME)
    slug = models.SlugField(max_length=MAX_LENGTH_SLUG, unique=True)

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        ordering = ('name',)

    def __str__(self):
        return self.name


class Genre(models.Model):
    name = models.CharField(max_length=MAX_LENGTH_NAME)
    slug = models.SlugField(max_length=MAX_LENGTH_SLUG, unique=True)

    class Meta:
        verbose_name = 'Жанр'
        verbose_name_plural = 'Жанры'
        ordering = ('name',)

    def __str__(self):
        return self.name


class Title(models.Model):
    name = models.CharField(max_length=MAX_LENGTH_NAME)
    year = models.PositiveSmallIntegerField(
        validators=(
            MinValueValidator(1),
            validate_year_not_future,
        ),
        verbose_name='Год выпуска',
    )
    description = models.TextField(blank=True)
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        related_name='titles',
    )
    genre = models.ManyToManyField(
        Genre,
        related_name='titles',
    )

    class Meta:
        verbose_name = 'Произведение'
        verbose_name_plural = 'Произведения'
        ordering = ('name',)

    def __str__(self):
        return f'{self.name}: {self.year}, {self.description}'


class Review(models.Model):
    title = models.ForeignKey(Title,
                              on_delete=models.CASCADE,
                              related_name='reviews')
    author = models.ForeignKey(User,
                               on_delete=models.CASCADE,
                               related_name='reviews')
    text = models.TextField()
    score = models.PositiveSmallIntegerField(validators=[
        MinValueValidator(MIN_SCORE),
        MaxValueValidator(MAX_SCORE)])
    pub_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'
        unique_together = ('title', 'author')
        ordering = ('-pub_date',)

    def __str__(self):
        return (f'{self.author}: {self.title}, {self.score}. '
                f'{self.text[:MAX_LENGTH_TEXT_STR]}')


class Comment(models.Model):
    review = models.ForeignKey(Review,
                               on_delete=models.CASCADE,
                               related_name='comments')
    author = models.ForeignKey(User,
                               on_delete=models.CASCADE,
                               related_name='comments')
    text = models.TextField()
    pub_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'
        ordering = ('-pub_date',)

    def __str__(self):
        return (f'{self.author}: {self.review}. '
                f'{self.text[:MAX_LENGTH_TEXT_STR]}')
