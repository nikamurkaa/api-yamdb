from django.core.validators import RegexValidator
from rest_framework import serializers
from reviews.models import Category, Comment, Genre, Review, Title

from users.models import User


class ReviewSerializer(serializers.ModelSerializer):
    """Сериализатор для отзывов."""
    author = serializers.SlugRelatedField(slug_field='username',
                                          read_only=True)

    class Meta:
        model = Review
        fields = '__all__'
        read_only_fields = ('title', 'author', 'pub_date')

    def validate(self, data):
        if self.context['request'].method == 'POST':
            if Review.objects.filter(
                title_id=self.context['view'].kwargs['title_id'],
                author=self.context['request'].user
            ).exists():
                raise serializers.ValidationError(
                    'Вы уже оставляли отзыв.')
        return data


class CommentSerializer(serializers.ModelSerializer):
    """Сериализатор для комментариев."""
    author = serializers.SlugRelatedField(slug_field='username',
                                          read_only=True)

    class Meta:
        model = Comment
        fields = ('id', 'text', 'author', 'pub_date')
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
    rating = serializers.IntegerField(read_only=True)

    class Meta:
        model = Title
        fields = ('id', 'name', 'year', 'rating', 'description',
                  'genre', 'category')


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
        fields = ('id', 'name', 'year', 'description',
                  'genre', 'category')


class SignUpSerializer(serializers.Serializer):
    username = serializers.CharField(
        max_length=150,
        validators=[
            RegexValidator(
                regex=r'^[\w.@+-]+\Z',
                message='Username может содержать только буквы, цифры и символы . @ + - _'
            )
        ]
    )
    email = serializers.EmailField(max_length=254)

    def validate_username(self, value):
        if value.lower() == 'me':
            raise serializers.ValidationError('Username "me" запрещён')
        return value

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
            # Если email новый, проверяем username на уникальность
            if User.objects.filter(username=username).exists():
                raise serializers.ValidationError(
                    {'username': 'Пользователь с таким username уже существует.'}
                )
        return data

class TokenSerializer(serializers.Serializer):
    username = serializers.CharField()
    confirmation_code = serializers.CharField()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'bio', 'role')
        read_only_fields = ('role',)  # роль нельзя менять через профиль

class AdminUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'bio', 'role')
