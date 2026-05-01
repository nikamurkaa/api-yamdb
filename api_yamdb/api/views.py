from django.contrib.auth import get_user_model
from django.db.models import Avg
from django.db.models.functions import Round
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import (filters, generics, mixins,
                            permissions, viewsets)
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import AccessToken
from reviews.models import Category, Genre, Review, Title
from .constants import (READ_UPDATE_METHODS, FULL_CRUD_METHODS)
from .filters import TitleFilter
from .permissions import (IsAdmin, IsAdminOrReadOnly,
                          IsOwnerOrModeratorOrAdminReadOnly)
from .serializers import (AdminUserSerializer, CategorySerializer,
                          CommentSerializer, GenreSerializer, ReviewSerializer,
                          SignUpSerializer, TitleReadSerializer,
                          TitleWriteSerializer, TokenSerializer,
                          UserSerializer)

User = get_user_model()


class ReviewCommentBaseViewSet(viewsets.ModelViewSet):
    """Базовый вьюсет для отзывов и комментариев."""

    http_method_names = FULL_CRUD_METHODS
    permission_classes = (IsOwnerOrModeratorOrAdminReadOnly,)


class ReviewViewSet(ReviewCommentBaseViewSet):
    """Viewset для отзывов."""

    serializer_class = ReviewSerializer

    def get_title(self):
        if 'title_id' not in self.kwargs:
            raise NotFound(detail='В запросе не указан id произведения.')
        return get_object_or_404(Title, pk=self.kwargs['title_id'])

    def get_queryset(self):
        return self.get_title().reviews.all()

    def perform_create(self, serializer):
        serializer.save(author=self.request.user, title=self.get_title())


class CommentViewSet(ReviewCommentBaseViewSet):
    """Viewset для комментариев."""

    serializer_class = CommentSerializer

    def get_review(self):
        if 'title_id' not in self.kwargs:
            raise NotFound(detail='В запросе не указан id произведения.')
        if 'review_id' not in self.kwargs:
            raise NotFound(detail='В запросе не указан id отзыва.')
        return get_object_or_404(Review, pk=self.kwargs['review_id'],
                                 title_id=self.kwargs['title_id'])

    def get_queryset(self):
        return self.get_review().comments.all()

    def perform_create(self, serializer):
        serializer.save(author=self.request.user,
                        review=self.get_review())


class BaseCategoryGenreViewSet(mixins.ListModelMixin,
                               mixins.CreateModelMixin,
                               mixins.DestroyModelMixin,
                               viewsets.GenericViewSet):
    """Базовый вьюсет для категории и жанра"""

    permission_classes = (IsAdminOrReadOnly,)
    filter_backends = (filters.SearchFilter,)
    search_fields = ('name',)
    lookup_field = 'slug'


class CategoryViewSet(BaseCategoryGenreViewSet):
    """Viewset для категорий произведений."""

    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class GenreViewSet(BaseCategoryGenreViewSet):
    """Viewset для жанров произведений."""

    queryset = Genre.objects.all()
    serializer_class = GenreSerializer


class TitleViewSet(viewsets.ModelViewSet):
    """Viewset для произведений."""

    http_method_names = FULL_CRUD_METHODS
    permission_classes = (IsAdminOrReadOnly,)
    filter_backends = (DjangoFilterBackend, filters.OrderingFilter)
    filterset_class = TitleFilter
    ordering_fields = ('name', 'year', 'genre')

    def get_queryset(self):
        return Title.objects.select_related('category').prefetch_related(
            'genre'
        ).annotate(rating=Round(Avg('reviews__score')))

    def get_serializer_class(self):
        if self.action in {'list', 'retrieve'}:
            return TitleReadSerializer
        return TitleWriteSerializer


class SignUpView(generics.CreateAPIView):
    """Регистрация пользователя и отправка кода подтверждения."""

    serializer_class = SignUpSerializer
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class TokenView(generics.CreateAPIView):
    """Получение JWT-токена по username и confirmation_code."""

    serializer_class = TokenSerializer
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = User.objects.get(username=serializer.validated_data['username'])
        token = AccessToken.for_user(user)
        return Response({'token': str(token)})


class UserViewSet(viewsets.ModelViewSet):
    """Управление пользователями (только для администратора)."""

    http_method_names = FULL_CRUD_METHODS
    queryset = User.objects.all()
    serializer_class = AdminUserSerializer
    permission_classes = (IsAdmin,)
    lookup_field = 'username'
    filter_backends = (filters.SearchFilter,)
    search_fields = ('username',)


class ProfileView(generics.RetrieveUpdateAPIView):
    """Профиль текущего пользователя."""

    http_method_names = READ_UPDATE_METHODS
    serializer_class = UserSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        return self.request.user
