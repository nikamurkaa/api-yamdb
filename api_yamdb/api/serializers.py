from django.contrib.auth import get_user_model
from django.db.models import Avg
from django.utils import timezone
from django.core.validators import RegexValidator
from rest_framework import serializers
from reviews.models import Category, Comment, Genre, Review, Title

User = get_user_model()


def validate_username_not_me(username: str):
    """Проверяет, что username не равен зарезервированному значению me."""

    if username.lower() == 'me':
        raise serializers.ValidationError('Username "me" запрещён.')
    return username


class ReviewSerializer(serializers.ModelSerializer):
    """Сериализатор для отзывов."""

    author = serializers.SlugRelatedField(slug_field='username',
                                          read_only=True)

    class Meta:
        model = Review
        fields = '__all__'
        read_only_fields = ('title',)

    def validate(self, data):
        request = self.context.get('request')
        view = self.context.get('view')

        if not (request and request.method == 'POST' and view):
            return data

        title_id = view.kwargs.get('title_id')
        if request.user.reviews.filter(title_id=title_id).exists():
            raise serializers.ValidationError('Вы уже оставляли отзыв.')

        return data


class CommentSerializer(serializers.ModelSerializer):
    """Сериализатор для комментариев."""

    author = serializers.SlugRelatedField(slug_field='username',
                                          read_only=True)

    class Meta:
        model = Comment
        fields = '__all__'
        read_only_fields = ('author', 'pub_date', 'review')


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
    rating = serializers.SerializerMethodField()

    class Meta:
        model = Title
        fields = ('id', 'name', 'year', 'rating', 'description',
                  'genre', 'category')

    def get_rating(self, obj):
        rating = getattr(obj, 'rating', None)
        if rating is None:
            rating = obj.reviews.aggregate(Avg('score')).get('score__avg')
        if rating is None:
            return None
        return int(rating)


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
    )

    class Meta:
        model = Title
        fields = '__all__'
        read_only_fields = ('id', 'rating')

    def validate_year(self, value):
        if value > timezone.now().year:
            raise serializers.ValidationError(
                'Год выпуска не может быть больше текущего.'
            )
        return value

    def to_representation(self, instance):
        return TitleReadSerializer(instance).data


class SignUpSerializer(serializers.Serializer):
    username = serializers.CharField(
        max_length=150,
        validators=[
            RegexValidator(
                regex=r'^[\w.@+-]+\Z',
                message=(
                    'Username может содержать только буквы, цифры '
                    'и символы . @ + - _'
                )
            )
        ]
    )
    email = serializers.EmailField(max_length=254)

    def validate_username(self, value):
        return validate_username_not_me(value)

    def validate(self, data):
        email = data.get('email')
        username = data.get('username')
        user_by_email = User.objects.filter(email=email).first()
        if user_by_email:
            if user_by_email.username != username:
                raise serializers.ValidationError(
                    {'email': 'Пользователь с таким email уже существует.'}
                )
        else:
            if User.objects.filter(username=username).exists():
                raise serializers.ValidationError({
                    'username': 'Пользователь с таким username уже существует.'
                })
        return data


class TokenSerializer(serializers.Serializer):
    username = serializers.CharField()
    confirmation_code = serializers.CharField()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'username', 'email', 'first_name',
            'last_name', 'bio', 'role',
        )
        read_only_fields = ('role',)

    def validate_username(self, value):
        return validate_username_not_me(value)


class AdminUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'username', 'email', 'first_name',
            'last_name', 'bio', 'role',
        )

    def validate_username(self, value):
        return validate_username_not_me(value)
