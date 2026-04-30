from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.validators import UnicodeUsernameValidator
from rest_framework import serializers
from rest_framework.exceptions import NotFound
from reviews.models import Category, Comment, Genre, Review, Title
from users.models import EMAIL_MAX_LENGTH, USERNAME_MAX_LENGTH
from users.validators import validate_username_not_me

User = get_user_model()


class AuthorReadOnlySerializer(serializers.ModelSerializer):
    author = serializers.SlugRelatedField(
        slug_field='username',
        read_only=True,
    )


class ReviewSerializer(AuthorReadOnlySerializer):
    """Сериализатор для отзывов."""

    class Meta:
        model = Review
        fields = ('id', 'text', 'author', 'score', 'pub_date')
        read_only_fields = ('author', 'pub_date')

    def validate(self, data):
        request = self.context.get('request')
        view = self.context.get('view')
        if not request or not view or request.method != 'POST':
            return data

        title_id = view.kwargs.get('title_id')
        if request.user.reviews.filter(title_id=title_id).exists():
            raise serializers.ValidationError('Вы уже оставляли отзыв.')
        return data


class CommentSerializer(AuthorReadOnlySerializer):
    """Сериализатор для комментариев."""

    class Meta:
        model = Comment
        fields = ('id', 'text', 'author', 'pub_date')
        read_only_fields = ('author', 'pub_date')


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


class SignUpSerializer(serializers.Serializer):
    """Сериализатор регистрации пользователя."""

    username = serializers.CharField(
        max_length=USERNAME_MAX_LENGTH,
        validators=(UnicodeUsernameValidator(), validate_username_not_me),
    )
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


class TokenSerializer(serializers.Serializer):
    """Сериализатор получения JWT-токена."""

    username = serializers.CharField(
        max_length=USERNAME_MAX_LENGTH,
        validators=(UnicodeUsernameValidator(), validate_username_not_me),
    )
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
        data['user'] = user
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
