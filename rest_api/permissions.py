from rest_framework.permissions import BasePermission


class IsPrivileged(BasePermission):
    """
    Allows access only to privileged users.
    """

    def has_permission(self, request, view):
        return request.user and request.user.employee_type == "PRIVILEGED"


class IsGeneral(BasePermission):
    """
    Allows access only to general users.
    """

    def has_permission(self, request, view):
        return request.user and request.user.employee_type == "GENERAL"


class IsOwner(BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """

    def has_object_permission(self, request, view, obj):
        return obj.employee == request.user
