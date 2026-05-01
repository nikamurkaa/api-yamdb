from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.mail import send_mail
from rest_framework import serializers
from rest_framework.exceptions import NotFound

from reviews.models import Category, Comment, Genre, Review, Title
from users.models import EMAIL_MAX_LENGTH, USERNAME_MAX_LENGTH
from users.validators import validate_username_not_reserved

User = get_user_model()


class AuthorFieldMixin:
    """Миксин с полем для автора"""

    author = serializers.SlugRelatedField(
        slug_field='username',
        read_only=True,
    )


class UsernameFieldMixin:
    """Миксин с полем для имени пользователя"""
    
    username = serializers.CharField(
        max_length=USERNAME_MAX_LENGTH,
        validators=(UnicodeUsernameValidator(),
                    validate_username_not_reserved),
    )


class ReviewSerializer(AuthorFieldMixin, serializers.ModelSerializer):
    """Сериализатор для отзывов."""

    class Meta:
        model = Review
        fields = ('id', 'text', 'author', 'score', 'pub_date')
        read_only_fields = ('title',)

    def validate(self, data):
        request = self.context.get('request')
        view = self.context.get('view')
        if not request or not view or request.method != 'POST':
            return data
        if 'title_id' not in view.kwargs:
            raise NotFound('Отсутствует id произведения.')
        if request.user.reviews.filter(
            title_id=view.kwargs['title_id']
        ).exists():
            raise serializers.ValidationError('Вы уже оставляли отзыв.')
        return data


class CommentSerializer(AuthorFieldMixin, serializers.ModelSerializer):
    """Сериализатор для комментариев."""

    class Meta:
        model = Comment
        fields = ('id', 'text', 'author', 'pub_date')
        read_only_fields = ('review',)


class CategorySerializer(serializers.ModelSerializer):
    """Сериализатор для категорий произведений."""

    class Meta:
        model = Category
        fields = ('name', 'slug')


class GenreSerializer(serializers.ModelSerializer):
    """Сериализатор для жанров произведений."""

    class Meta:
        model = Genre
        fields = ('name', 'slug')


class TitleReadSerializer(serializers.ModelSerializer):
    """Сериализатор для чтения произведений."""

    category = CategorySerializer()
    genre = GenreSerializer(many=True)
    rating = serializers.IntegerField(read_only=True, default=None)

    class Meta:
        model = Title
        fields = (
            'id', 'name', 'year', 'rating',
            'description', 'genre', 'category',
        )


class TitleWriteSerializer(serializers.ModelSerializer):
    """Сериализатор для создания/обновления произведений."""

    category = serializers.SlugRelatedField(
        slug_field='slug',
        queryset=Category.objects.all(),
    )
    genre = serializers.SlugRelatedField(
        slug_field='slug',
        queryset=Genre.objects.all(),
        many=True,
        allow_empty=False,
    )

    class Meta:
        model = Title
        fields = '__all__'
        read_only_fields = ('rating',)

    def to_representation(self, instance):
        return TitleReadSerializer(instance).data


class SignUpSerializer(UsernameFieldMixin, serializers.ModelSerializer):
    """Сериализатор регистрации пользователя."""

    email = serializers.EmailField(max_length=EMAIL_MAX_LENGTH)

    def validate(self, data):
        email = data.get('email')
        username = data.get('username')
        username_exists = User.objects.filter(
            username=username,
        ).exclude(email=email).exists()
        email_exists = User.objects.filter(
            email=email,
        ).exclude(username=username).exists()

        if username_exists:
            raise serializers.ValidationError({
                'username': 'Пользователь с таким username уже существует.'
            })
        if email_exists:
            raise serializers.ValidationError(
                {'email': 'Пользователь с таким email уже существует.'}
            )
        return data

    def create(self, validated_data):
        username = validated_data['username']
        email = validated_data['email']
        user, created = User.objects.get_or_create(
            username=username,
            defaults={'email': email},
        )
        if created:
            user.set_unusable_password()
            user.save(update_fields=('password',))
        confirmation_code = default_token_generator.make_token(user)
        send_mail(
            subject='Код подтверждения YaMDb',
            message=f'Ваш код подтверждения: {confirmation_code}',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=(email,),
            fail_silently=True,
        )

        return user


class TokenSerializer(UsernameFieldMixin, serializers.ModelSerializer):
    """Сериализатор получения JWT-токена."""

    confirmation_code = serializers.CharField()

    def validate(self, data):
        username = data.get('username')
        confirmation_code = data.get('confirmation_code')
        user = User.objects.filter(username=username).first()
        if user is None:
            raise NotFound('Пользователь не найден.')
        if not default_token_generator.check_token(user, confirmation_code):
            raise serializers.ValidationError({
                'confirmation_code': 'Неверный код подтверждения.'
            })
        return data


class AdminUserSerializer(serializers.ModelSerializer):
    """Сериализатор управления пользователями для администратора."""

    class Meta:
        model = User
        fields = (
            'username', 'email', 'first_name',
            'last_name', 'bio', 'role',
        )

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class UserSerializer(AdminUserSerializer):
    """Сериализатор профиля текущего пользователя."""

    class Meta(AdminUserSerializer.Meta):
        read_only_fields = ('role',)
