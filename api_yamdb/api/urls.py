from django.urls import include, path
from rest_framework import routers

from api.views import CategoryViewSet

v1_router = routers.DefaultRouter()
v1_router.register('categories', CategoryViewSet, basename='category')

urlpatterns = [
    path('', include(v1_router.urls)),
]