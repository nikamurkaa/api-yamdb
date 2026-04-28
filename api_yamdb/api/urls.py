from django.urls import include, path
from rest_framework import routers

from .views import (CategoryViewSet, CommentViewSet,
                    GenreViewSet, ReviewViewSet,
                    TitleViewSet)

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

urlpatterns = [
    path('', include(v1_router.urls)),
]
