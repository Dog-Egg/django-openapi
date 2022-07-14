from django.http import HttpRequest


class PermissionABC:
    def has_permission(self, request: HttpRequest):
        raise NotImplementedError


class IsAuthenticated(PermissionABC):
    def has_permission(self, request: HttpRequest):
        return bool(request.user and request.user.is_authenticated)
