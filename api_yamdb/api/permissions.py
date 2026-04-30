from rest_framework.permissions import (BasePermission,
                                        IsAuthenticatedOrReadOnly,
                                        SAFE_METHODS)


class IsAdmin(BasePermission):
    """Разрешает доступ только администраторам."""

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_admin


class IsOwnerOrModeratorOrAdminReadOnly(IsAuthenticatedOrReadOnly):
    """Разрешает изменение автору, модератору или администратору."""

    def has_object_permission(self, request, view, review_or_comment):
        if request.method in SAFE_METHODS:
            return True
        return (review_or_comment.author == request.user
                or request.user.is_moderator
                or request.user.is_admin)


class IsAdminOrReadOnly(BasePermission):
    """Разрешает изменение только администратору, чтение — всем."""

    def has_permission(self, request, view):
        return (
            request.method in SAFE_METHODS
            or (request.user.is_authenticated and request.user.is_admin)
        )
