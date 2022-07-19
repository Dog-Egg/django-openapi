from django.http import HttpRequest

from openapi.http.exceptions import abort


class PermissionABC:
    def check_permission(self, request):
        raise NotImplementedError

    def to_spec(self):
        return [{'_$unknown$_': []}]


class DjangoPermission(PermissionABC):
    def has_permission(self, request: HttpRequest):
        return True

    def check_permission(self, request):
        if not self.has_permission(request):
            if request.user and request.user.is_authenticated:
                abort(403)
            abort(401)

    def to_spec(self):
        # TODO get settings
        return super().to_spec()


class IsAuthenticated(DjangoPermission):
    def has_permission(self, request: HttpRequest):
        return bool(request.user and request.user.is_authenticated)
