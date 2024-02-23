from django.conf import settings

from rest_framework.permissions import BasePermission
from uuid import UUID

from users.models import User, UserRole


class ACWBasePermission(BasePermission):
    def has_api_permission(self, request):
        if (
            request.resolver_match.app_name in settings.API_APP_SETTINGS["PUBLIC"]
            or request.resolver_match.app_name
            not in settings.API_APP_SETTINGS["PROTECTED"]
        ):
            return True

        app_name = request.resolver_match.app_name
        method = request.method.lower()
        endpoint = request.resolver_match.route.split("/")[1]
        api_call = f"{app_name}_{method}_{endpoint}"

        api_permissions = list(
            request.user.role.api_permissions.values_list(
                "codename",
                flat=True,
            )
        )

        return api_call in api_permissions


class IsVisitor(ACWBasePermission):
    def has_permission(self, request, view):
        permission = (
            request.user
            and isinstance(request.user, User)
            and request.user.role.name == UserRole.VISITOR
        )
        return permission


class ACWIsAuthenticated(ACWBasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)


class IsOwner(ACWIsAuthenticated):
    def has_object_permission(self, request, view, obj):
        obj_user = self.get_object_user(obj)

        # No restrictions if model has no relations with User,
        if obj_user is None:
            return True

        return obj_user == request.user

    def get_object_user(self, obj):
        obj_user = None

        if isinstance(obj, User):
            obj_user = obj
        elif hasattr(obj, "user"):
            obj_user = obj.user
        elif type(obj) is dict and "user" in obj:
            if isinstance(obj["user"], User):
                obj_user = obj["user"]
            else:
                user_uuid = (
                    UUID(obj["user"]) if type(obj["user"]) is str else obj["user"]
                )
                try:
                    obj_user = User.objects.get(uuid=user_uuid)
                except User.DoesNotExist:
                    pass

        return obj_user


class IsUser(IsOwner):
    def has_permission(self, request, view):
        is_authenticated = super(IsUser, self).has_permission(request, view)

        permission = (
            is_authenticated
            and isinstance(request.user, User)
            and request.user.role.name == UserRole.USER
        )

        return permission


class IsAffiliate(IsOwner):
    def has_permission(self, request, view):
        is_authenticated = super(IsAffiliate, self).has_permission(request, view)

        permission = (
            is_authenticated
            and isinstance(request.user, User)
            and request.user.role.name == UserRole.AFFILIATE
        )

        return permission


class IsManager(IsOwner):
    def has_permission(self, request, view):
        is_authenticated = super(IsManager, self).has_permission(request, view)

        permission = is_authenticated and request.user.role.name == UserRole.MANAGER

        return permission

    def has_object_permission(self, request, view, obj):
        obj_user = self.get_object_user(obj)

        is_owner = super(IsManager, self).has_object_permission(request, view, obj)
        is_manager = request.user.managed_users.filter(managed_user=obj_user)

        return is_owner or (is_manager and self.has_api_permission(request))


class IsInternal(ACWIsAuthenticated):
    def has_permission(self, request, view):
        is_authenticated = super(IsInternal, self).has_permission(request, view)

        permission = (
            is_authenticated
            and request.user.role.name == UserRole.INTERNAL_USER
            and self.has_api_permission(request)
        )

        return permission

    def has_api_permission(self, request):
        if (
            "root" in request.resolver_match.url_name
            or request.resolver_match.url_name in settings.API_APP_SETTINGS["INTERNAL"]
        ):
            return True

        return super().has_api_permission(request)


class IsAdmin(ACWIsAuthenticated):
    def has_permission(self, request, view):
        is_authenticated = super(IsAdmin, self).has_permission(request, view)
        permission = is_authenticated and request.user.role.name == UserRole.ADMIN
        return permission


class IsAdminOrIsSelf(BasePermission):
    def has_object_permission(self, request, view, obj):
        if IsAdmin().has_permission(request, view):
            return True
        else:
            return obj == request.user


class IsInternalOrAdmin(BasePermission):
    """For drf-spectacular since it doesn't accept | on class strings"""

    def has_permission(self, request, view):
        internal_permission = IsInternal().has_permission(request, view)
        admin_permission = IsAdmin().has_permission(request, view)
        return internal_permission or admin_permission


class IsSuperuser(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_superuser)
