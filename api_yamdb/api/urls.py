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
v1_router.register(r'titles/(?P<title_id>\d+)/reviews',
                   ReviewViewSet, basename='title-reviews')
v1_router.register(
    r'titles/(?P<title_id>\d+)/reviews/(?P<review_id>\d+)/comments',
    CommentViewSet, basename='review-comments')
v1_router.register(r'users', UserViewSet, basename='user')

auth_patterns = [
    path('signup/', SignUpView.as_view(), name='signup'),
    path('token/', TokenView.as_view(), name='token'),
]
urlpatterns = [
    path('auth/', include(auth_patterns)),
    path('users/me/', ProfileView.as_view(), name='profile'),
    path('', include(v1_router.urls)),
]
