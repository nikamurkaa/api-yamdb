from django.urls import include, path
from rest_framework import routers

from .views import (CategoryViewSet, CommentViewSet,
                    GenreViewSet, ReviewViewSet,
                    TitleViewSet)

from .views import SignUpView, TokenView, UserViewSet, ProfileView

v1_router = routers.DefaultRouter()
v1_router.register(r'categories',
                   CategoryViewSet, basename='category')
v1_router.register(r'genres',
                   GenreViewSet, basename='genre')
v1_router.register(r'titles',
                   TitleViewSet, basename='title')
v1_router.register(r'reviews',
                   ReviewViewSet, basename='review')
v1_router.register(r'reviews/(?P<review_id>\d+)/comments',
                   CommentViewSet, basename='review-comments')
v1_router.register('users', UserViewSet, basename='user')

urlpatterns = [
    path('auth/signup/', SignUpView.as_view(), name='signup'),
    path('auth/token/', TokenView.as_view(), name='token'),
    path('users/me/', ProfileView.as_view(), name='profile'),
    path('', include(v1_router.urls)),
]
