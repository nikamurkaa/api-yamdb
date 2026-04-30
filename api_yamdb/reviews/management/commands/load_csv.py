import csv

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from reviews.models import Category, Comment, Genre, Review, Title

User = get_user_model()

DEFAULT_USER_ROLE = 'user'


class Command(BaseCommand):
    """Команда для импорта начальных данных проекта из CSV."""

    help = 'Загружает данные из CSV-файлов в базу данных.'
    data_dir = settings.BASE_DIR / 'static' / 'data'

    def handle(self, *args, **options):
        """Запускает импорт CSV-файлов в правильном порядке."""
        loaders = (
            self._load_users,
            self._load_categories,
            self._load_genres,
            self._load_titles,
            self._load_genre_title,
            self._load_reviews,
            self._load_comments,
        )
        for loader in loaders:
            loader()
        self.stdout.write(
            self.style.SUCCESS('Данные из CSV успешно загружены.')
        )

    def _get_file_path(self, filename):
        """Возвращает путь к CSV-файлу и проверяет его наличие."""
        file_path = self.data_dir / filename
        if not file_path.exists():
            raise CommandError(f'Файл {file_path} не найден.')
        return file_path

    def _read_csv(self, filename):
        """Читает CSV-файл и возвращает строки в виде словарей."""
        file_path = self._get_file_path(filename)
        with file_path.open(encoding='utf-8-sig', newline='') as csv_file:
            yield from csv.DictReader(csv_file)

    def _get_int(self, row, field_name):
        """Возвращает числовое значение поля из строки CSV."""
        raw_value = row.get(field_name)
        try:
            return int(raw_value)
        except (TypeError, ValueError) as error:
            raise CommandError(
                f'В поле {field_name} указано не число: {raw_value}'
            ) from error

    def _get_optional_int(self, row, field_name):
        """Возвращает число или None для необязательного поля CSV."""
        value = row.get(field_name)
        if not value:
            return None
        return self._get_int(row, field_name)

    def _parse_datetime(self, value):
        """Преобразует строку из CSV в объект даты и времени."""
        date_time = parse_datetime(value)
        if date_time is None:
            raise CommandError(f'Некорректное значение даты: {value}')
        if timezone.is_naive(date_time):
            date_time = timezone.make_aware(date_time)
        return date_time

    def _update_pub_date(self, model, object_id, value):
        """Обновляет дату публикации у объекта после его создания."""
        if value:
            model.objects.filter(id=object_id).update(
                pub_date=self._parse_datetime(value)
            )

    def _get_object(self, model, object_id):
        """Возвращает объект модели или сообщает об ошибке импорта."""
        try:
            return model.objects.get(id=object_id)
        except model.DoesNotExist as error:
            raise CommandError(
                f'Объект {model.__name__} с id={object_id} не найден.'
            ) from error

    def _load_users(self):
        """Загружает пользователей из файла users.csv."""
        for row in self._read_csv('users.csv'):
            user, created = User.objects.update_or_create(
                id=self._get_int(row, 'id'),
                defaults={
                    'username': row['username'],
                    'email': row['email'],
                    'role': row.get('role') or DEFAULT_USER_ROLE,
                    'bio': row.get('bio') or '',
                    'first_name': row.get('first_name') or '',
                    'last_name': row.get('last_name') or '',
                },
            )
            if created:
                user.set_unusable_password()
                user.save(update_fields=('password',))

    def _load_categories(self):
        """Загружает категории произведений из файла category.csv."""
        for row in self._read_csv('category.csv'):
            Category.objects.update_or_create(
                id=self._get_int(row, 'id'),
                defaults={
                    'name': row['name'],
                    'slug': row['slug'],
                },
            )

    def _load_genres(self):
        """Загружает жанры произведений из файла genre.csv."""
        for row in self._read_csv('genre.csv'):
            Genre.objects.update_or_create(
                id=self._get_int(row, 'id'),
                defaults={
                    'name': row['name'],
                    'slug': row['slug'],
                },
            )

    def _load_titles(self):
        """Загружает произведения из файла titles.csv."""
        for row in self._read_csv('titles.csv'):
            Title.objects.update_or_create(
                id=self._get_int(row, 'id'),
                defaults={
                    'name': row['name'],
                    'year': self._get_int(row,
                                          'year'),
                    'category_id': self._get_optional_int(row,
                                                          'category'),
                },
            )

    def _load_genre_title(self):
        """Загружает связи произведений и жанров из genre_title.csv."""
        for row in self._read_csv('genre_title.csv'):
            title = self._get_object(
                Title,
                self._get_int(row, 'title_id')
            )
            genre = self._get_object(
                Genre,
                self._get_int(row, 'genre_id')
            )
            title.genre.add(genre)

    def _load_reviews(self):
        """Загружает отзывы из файла review.csv."""
        for row in self._read_csv('review.csv'):
            review, _ = Review.objects.update_or_create(
                id=self._get_int(row, 'id'),
                defaults={
                    'title_id': self._get_int(row, 'title_id'),
                    'author_id': self._get_int(row, 'author'),
                    'text': row['text'],
                    'score': self._get_int(row, 'score'),
                },
            )
            self._update_pub_date(Review,
                                  review.id,
                                  row.get('pub_date'))

    def _load_comments(self):
        """Загружает комментарии из файла comments.csv."""
        for row in self._read_csv('comments.csv'):
            comment, _ = Comment.objects.update_or_create(
                id=self._get_int(row, 'id'),
                defaults={
                    'review_id': self._get_int(row, 'review_id'),
                    'author_id': self._get_int(row, 'author'),
                    'text': row['text'],
                },
            )
            self._update_pub_date(Comment,
                                  comment.id,
                                  row.get('pub_date'))
