from django.core.validators import MaxValueValidator, MinValueValidator
from django.contrib.auth import get_user_model
from django.db import models

from .constants import (MAX_LENGTH_NAME, MAX_LENGTH_SLUG,
                        MIN_SCORE, MAX_SCORE, MAX_LENGTH_TEXT_STR)
from .validators import validate_year_not_future

User = get_user_model()


class NamedSluggedModel(models.Model):
    """Абстрактная модель с общими полями для категорий и жанров."""

    name = models.CharField(
        max_length=MAX_LENGTH_NAME,
        verbose_name='название'
    )
    slug = models.SlugField(
        max_length=MAX_LENGTH_SLUG,
        unique=True,
        verbose_name='слаг'
    )

    class Meta:
        abstract = True
        ordering = ('name',)

    def __str__(self):
        return self.name


class Category(NamedSluggedModel):
    """Категория."""

    class Meta(NamedSluggedModel.Meta):
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'


class Genre(NamedSluggedModel):
    """Жанр."""

    class Meta(NamedSluggedModel.Meta):
        verbose_name = 'Жанр'
        verbose_name_plural = 'Жанры'


class Title(models.Model):
    """Произведение."""

    name = models.CharField(max_length=MAX_LENGTH_NAME,
                            verbose_name='название')
    year = models.PositiveSmallIntegerField(
        validators=(
            MinValueValidator(1),
            validate_year_not_future,
        ),
        verbose_name='Год выпуска',
    )
    description = models.TextField(blank=True, verbose_name='описание')
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        related_name='titles',
        verbose_name='категория'
    )
    genre = models.ManyToManyField(
        Genre,
        related_name='titles',
        verbose_name='жанр'
    )

    class Meta:
        verbose_name = 'Произведение'
        verbose_name_plural = 'Произведения'
        ordering = ('name',)

    def __str__(self):
        return f'{self.name}: {self.year}, {self.description}'


class Review(models.Model):
    """Отзыв."""

    title = models.ForeignKey(Title,
                              on_delete=models.CASCADE,
                              related_name='reviews',
                              verbose_name='произведение')
    author = models.ForeignKey(User,
                               on_delete=models.CASCADE,
                               related_name='reviews',
                               verbose_name='автор')
    text = models.TextField(verbose_name='текст')
    score = models.PositiveSmallIntegerField(validators=[
        MinValueValidator(MIN_SCORE),
        MaxValueValidator(MAX_SCORE)],
        verbose_name='оценка')
    pub_date = models.DateTimeField(auto_now_add=True,
                                    verbose_name='дата публикации',
                                    db_index=True)

    class Meta:
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'
        ordering = ('-pub_date',)
        constraints = [
            models.UniqueConstraint(
                fields=['title', 'author'],
                name='unique_title_author'
            ),
        ]

    def __str__(self):
        return (f'{self.author}: {self.title}, {self.score}. '
                f'{self.text[:MAX_LENGTH_TEXT_STR]}')


class Comment(models.Model):
    """Комментарий."""

    review = models.ForeignKey(Review,
                               on_delete=models.CASCADE,
                               related_name='comments',
                               verbose_name='отзыв')
    author = models.ForeignKey(User,
                               on_delete=models.CASCADE,
                               related_name='comments',
                               verbose_name='автор')
    text = models.TextField(verbose_name='текст')
    pub_date = models.DateTimeField(auto_now_add=True,
                                    verbose_name='дата публикации',
                                    db_index=True)

    class Meta:
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'
        ordering = ('-pub_date',)

    def __str__(self):
        return (f'{self.author}: {self.review}. '
                f'{self.text[:MAX_LENGTH_TEXT_STR]}')
