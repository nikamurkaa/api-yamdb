from django.urls import include, path
from rest_framework import routers

from api.views import CategoryViewSet, GenreViewSet

v1_router = routers.DefaultRouter()
v1_router.register('categories', CategoryViewSet, basename='category')
v1_router.register('genres', GenreViewSet, basename='genre')

urlpatterns = [
    path('', include(v1_router.urls)),
]