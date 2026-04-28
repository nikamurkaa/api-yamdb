import uuid

from django.db.models import Avg
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404
from rest_framework import (filters, viewsets,
                            status, viewsets,
                            generics, permissions)
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response

from reviews.models import Category, Genre, Title, Title, Review
from .permissions import IsAdminOrReadOnly, IsOwnerOrModeratorOrAdmin, IsAdmin
from .filters import TitleFilter
from .serializers import (CategorySerializer, CommentSerializer,
                          GenreSerializer, TitleReadSerializer,
                          TitleWriteSerializer, ReviewSerializer,
                          SignUpSerializer, TokenSerializer,
                          UserSerializer, AdminUserSerializer)

User = get_user_model()


class ReviewViewSet(viewsets.ModelViewSet):
    """Viewset для отзывов."""
    http_method_names = ['get', 'post', 'patch', 'delete'] 
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticatedOrReadOnly,
                          IsOwnerOrModeratorOrAdmin]

    def get_title_by_id(self):
        return get_object_or_404(Title, pk=self.kwargs['title_id'])

    def get_queryset(self):
        return self.get_title_by_id().reviews.all()

    def perform_create(self, serializer):
        serializer.save(
            author=self.request.user,
            title=self.get_title_by_id())


class CommentViewSet(viewsets.ModelViewSet):
    """Viewset для комментариев."""
    http_method_names = ['get', 'post', 'patch', 'delete'] 
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly,
                          IsOwnerOrModeratorOrAdmin]

    def get_review_by_id(self):
        return get_object_or_404(
            Review,
            pk=self.kwargs['review_id'],
            title_id=self.kwargs['title_id'],
        )

    def get_queryset(self):
        return self.get_review_by_id().comments.all()

    def perform_create(self, serializer):
        serializer.save(author=self.request.user,
                        review=self.get_review_by_id())


class CategoryViewSet(
    viewsets.mixins.ListModelMixin,
    viewsets.mixins.CreateModelMixin,
    viewsets.mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """Viewset для категорий произведений."""
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]
    pagination_class = LimitOffsetPagination
    filter_backends = (filters.SearchFilter,)
    search_fields = ('name',)
    lookup_field = 'slug'


class GenreViewSet(
    viewsets.mixins.ListModelMixin,
    viewsets.mixins.CreateModelMixin,
    viewsets.mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """Viewset для жанров произведений."""
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    permission_classes = [IsAdminOrReadOnly]
    pagination_class = LimitOffsetPagination
    filter_backends = (filters.SearchFilter,)
    search_fields = ('name',)
    lookup_field = 'slug'


class TitleViewSet(viewsets.ModelViewSet):
    """Viewset для произведений."""
    http_method_names = ['get', 'post', 'patch', 'delete']
    permission_classes = [IsAdminOrReadOnly]
    pagination_class = LimitOffsetPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = TitleFilter

    def get_queryset(self):
        return Title.objects.select_related('category').prefetch_related(
            'genre'
        ).annotate(rating=Avg('reviews__score'))

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return TitleReadSerializer
        return TitleWriteSerializer


class SignUpView(generics.CreateAPIView):
    serializer_class = SignUpSerializer
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        username = serializer.validated_data['username']
        email = serializer.validated_data['email']

        # Пытаемся найти пользователя по email
        user = User.objects.filter(email=email).first()
        if not user:
            user = User.objects.create_user(username=username, email=email)
        # Генерируем код подтверждения
        confirmation_code = str(uuid.uuid4())[:8]
        user.confirmation_code = confirmation_code
        user.save()

        send_mail(
            subject='Код подтверждения YaMDb',
            message=f'Ваш код подтверждения: {confirmation_code}',
            from_email=None,
            recipient_list=[email],
            fail_silently=True,  # Чтобы тесты не падали при ошибках почты
        )
        return Response(serializer.data, status=status.HTTP_200_OK)


class TokenView(generics.CreateAPIView):
    """Получение JWT-токена по username и confirmation_code."""
    serializer_class = TokenSerializer
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        username = serializer.validated_data['username']
        code = serializer.validated_data['confirmation_code']

        user = get_object_or_404(User, username=username)
        if user.confirmation_code != code:
            return Response(
                {'confirmation_code': 'Неверный код подтверждения'},
                status=status.HTTP_400_BAD_REQUEST
            )
        # Генерируем JWT
        refresh = RefreshToken.for_user(user)
        return Response({'token': str(refresh.access_token)})


class UserViewSet(viewsets.ModelViewSet):
    """Управление пользователями (только для администратора)."""
    http_method_names = ['get', 'post', 'patch', 'delete']
    queryset = User.objects.all()
    serializer_class = AdminUserSerializer
    permission_classes = (IsAdmin,)
    lookup_field = 'username'
    filter_backends = (filters.SearchFilter,)
    search_fields = ('username',)  # поле, по которому ищем


class ProfileView(generics.RetrieveUpdateAPIView):
    """Профиль текущего пользователя."""
    http_method_names = ['get', 'patch']
    serializer_class = UserSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        return self.request.user
