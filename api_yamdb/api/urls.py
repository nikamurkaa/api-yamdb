from django.urls import include, path
from rest_framework import routers

from api.views import CategoryViewSet, GenreViewSet

v1_router = routers.DefaultRouter()
v1_router.register('categories', CategoryViewSet, basename='categories')
v1_router.register('genres', GenreViewSet, basename='genres')

urlpatterns = [
    path('', include(v1_router.urls)),
]