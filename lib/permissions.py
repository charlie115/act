from rest_framework.permissions import BasePermission, IsAdminUser


def get_groups_name_lowercase(group_queryset):
    return [group.lower() for group in group_queryset.values_list("name", flat=True)]


class IsDjangoAdmin(IsAdminUser):
    def has_permission(self, request, view):
        return super(IsDjangoAdmin, self).has_permission(request, view)


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
