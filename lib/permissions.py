from rest_framework.permissions import BasePermission, IsAdminUser, IsAuthenticated

from users.models import User


def get_groups_name_lowercase(group_queryset):
    return [group.lower() for group in group_queryset.values_list("name", flat=True)]


class IsSuperuser(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_superuser)


class IsDjangoAdmin(IsSuperuser):
    def has_permission(self, request, view):
        superuser_permission = super(IsDjangoAdmin, self).has_permission(request, view)
        staff_permission = IsAdminUser().has_permission(request, view)

        return superuser_permission or staff_permission


class IsVisitor(IsSuperuser):
    def has_permission(self, request, view):
        superuser_permission = super(IsVisitor, self).has_permission(request, view)

        visitor_permission = bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == User.VISITOR
        )

        return superuser_permission or visitor_permission


class IsAuthenticatedOwner(IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        return obj.id == request.user if type(obj) is User else obj.user == request.user


class IsUser(IsSuperuser):
    def has_permission(self, request, view):
        superuser_permission = super(IsUser, self).has_permission(request, view)

        visitor_permission = bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == User.USER
        )

        return visitor_permission or superuser_permission


class IsACWAdmin(BasePermission):
    def has_permission(self, request, view):
        groups = get_groups_name_lowercase(request.user.groups)
        return bool(request.user and "admin" in groups)


class IsACWStaff(BasePermission):
    def has_permission(self, request, view):
        groups = get_groups_name_lowercase(request.user.groups)
        return bool(request.user and "staff" in groups)


class IsACWAffiliate(BasePermission):
    def has_permission(self, request, view):
        groups = get_groups_name_lowercase(request.user.groups)
        return bool(request.user and "affiliate" in groups)


class IsAdminOrIsSelf(BasePermission):
    def has_object_permission(self, request, view, obj):
        if IsDjangoAdmin().has_permission(request, view):
            return True
        else:
            return obj == request.user
