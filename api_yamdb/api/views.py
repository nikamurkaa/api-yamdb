import uuid

from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.db.models import Avg
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import (filters, generics, permissions,
                            status, viewsets)
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from reviews.models import Category, Genre, Title, Review
from .filters import TitleFilter
from .permissions import (IsAdmin, IsAdminOrReadOnly,
                          IsOwnerOrModeratorOrAdmin)
from .serializers import (AdminUserSerializer, CategorySerializer,
                          CommentSerializer, GenreSerializer,
                          ReviewSerializer, TitleReadSerializer,
                          TitleWriteSerializer, TokenSerializer,
                          SignUpSerializer, UserSerializer)

User = get_user_model()

FULL_CRUD_METHODS = ['get', 'post', 'patch', 'delete']
READ_CREATE_DELETE_METHODS = ['get', 'post', 'delete']
READ_UPDATE_METHODS = ['get', 'patch']


class ReviewViewSet(viewsets.ModelViewSet):
    """Viewset для отзывов."""
    http_method_names = FULL_CRUD_METHODS
    serializer_class = ReviewSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,
                          IsOwnerOrModeratorOrAdmin,)

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
    http_method_names = FULL_CRUD_METHODS
    serializer_class = CommentSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,
                          IsOwnerOrModeratorOrAdmin,)

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


class CategoryViewSet(viewsets.ModelViewSet):
    """Viewset для категорий произведений."""
    http_method_names = READ_CREATE_DELETE_METHODS
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = (IsAuthenticatedOrReadOnly, IsAdminOrReadOnly,)
    filter_backends = (filters.SearchFilter,)
    search_fields = ('name',)
    lookup_field = 'slug'

    def retrieve(self, request, *args, **kwargs):
        return Response(
            {'detail': 'Метод GET для отдельной категории запрещен.'},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )


class GenreViewSet(viewsets.ModelViewSet):
    """Viewset для жанров произведений."""
    http_method_names = READ_CREATE_DELETE_METHODS
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    permission_classes = (IsAuthenticatedOrReadOnly, IsAdminOrReadOnly,)
    filter_backends = (filters.SearchFilter,)
    search_fields = ('name',)
    lookup_field = 'slug'

    def retrieve(self, request, *args, **kwargs):
        return Response(
            {'detail': 'Метод GET для отдельного жанра запрещен.'},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )


class TitleViewSet(viewsets.ModelViewSet):
    """Viewset для произведений."""
    http_method_names = FULL_CRUD_METHODS
    permission_classes = (IsAuthenticatedOrReadOnly, IsAdminOrReadOnly,)
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
        user = User.objects.filter(email=email).first()
        if not user:
            user = User.objects.create_user(username=username, email=email)
        confirmation_code = str(uuid.uuid4())[:8]
        user.confirmation_code = confirmation_code
        user.save()
        send_mail(
            subject='Код подтверждения YaMDb',
            message=f'Ваш код подтверждения: {confirmation_code}',
            from_email=None,
            recipient_list=[email],
            fail_silently=True,
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
        refresh = RefreshToken.for_user(user)
        return Response({'token': str(refresh.access_token)})


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
