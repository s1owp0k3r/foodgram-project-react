from rest_framework import permissions


class IsAuthorOrReadOnly(permissions.BasePermission):
    """Разрешение для автора"""

    def has_permission(self, request, view):
        return (
            request.method in permissions.SAFE_METHODS
            or request.user.is_authenticated
        )

    def has_object_permission(self, request, view, obj):
        return (
            request.method in permissions.SAFE_METHODS
            or obj.author == request.user
        )


class UserProfilePermission(permissions.BasePermission):
    """Разрешение для просмотра профиля пользователя"""

    def has_permission(self, request, view):
        print(request.path.split('/')[-2:])
        return (
            request.path.split('/')[-2] != 'me'
            and request.method in permissions.SAFE_METHODS
            or request.user.is_authenticated
        )
