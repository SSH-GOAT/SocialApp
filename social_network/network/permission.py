from rest_framework.permissions import BasePermission

class AdminPermission(BasePermission):
    def has_permission(self, request, view):
        if request.method in ['DELETE']:
            return request.user.is_superuser