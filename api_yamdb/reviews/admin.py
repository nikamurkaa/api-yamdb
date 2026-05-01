from django.contrib import admin
from django.contrib.auth.models import Group

from .models import Category, Comment, Genre, Review, Title

admin.site.unregister(Group)
admin.site.register(Category)
admin.site.register(Genre)
admin.site.register(Title)
admin.site.register(Review)
admin.site.register(Comment)
