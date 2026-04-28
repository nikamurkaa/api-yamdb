from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from users.models import User


class Review(models.Model):
    title = models.ForeignKey(Title,
                              on_delete=models.CASCADE,
                              related_name='reviews')
    author = models.ForeignKey(User,
                               on_delete=models.CASCADE,
                               related_name='reviews')
    text = models.TextField()
    score = models.PositiveSmallIntegerField(validators=[
        MinValueValidator(1),
        MaxValueValidator(10)])
    pub_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'
        unique_together = ('title', 'author')
        ordering = ('-pub_date',)

    def __str__(self):
        return f'{self.author}: {self.title}, {self.score}. {self.text[:30]}'


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
        return f'{self.author}: {self.review}. {self.text[:30]}'
