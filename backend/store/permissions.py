from rest_framework.permissions import BasePermission


class IsMerchant(BasePermission):
    message = "仅商家账号可访问"

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.role in ("merchant", "console"))


class IsConsole(BasePermission):
    message = "仅平台账号可访问"

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.role == "console")
