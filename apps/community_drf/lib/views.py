from rest_framework import routers, viewsets
from rest_framework.utils.serializer_helpers import ReturnList

from lib.permissions import (
    ACWBasePermission,
    IsAdmin,
    IsInternal,
    IsManager,
    IsAffiliate,
    IsUser,
)
from users.models import User, UserRole


class BaseViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdmin | IsInternal | IsManager | IsAffiliate | IsUser]

    def get_queryset(self):
        queryset = super(BaseViewSet, self).get_queryset()

        """
        By default, filter queryset to own objects if model has relation to User.
        Else, return the queryset as is since there's no ownership.
        """

        query_field = ""
        query = {}

        if self.request.user:
            if queryset.model is User:
                query_field = "id__in"
                query = {query_field: [self.request.user.id]}

            elif hasattr(queryset.model, "user"):
                query_field = "user_id__in"
                query = {query_field: [self.request.user.id]}

            """
            Furthermore, depending on the caller's role, include in the queryset the objects they are allowed to manage
                Admin, Internal = all users
                Manager = managed users
                Others = self only
            """

            if isinstance(self.request.user, User):
                # If ADMIN, return all objects
                if self.request.user.role.name == UserRole.ADMIN:
                    return queryset

                # If INTERNAL, return all objects if has_api_permission
                if (
                    self.request.user.role.name == UserRole.INTERNAL_USER
                    and ACWBasePermission().has_api_permission(self.request)
                ):
                    return queryset

                # If MANAGER, return own (already filtered at the start) + managed users objects if has_api_permission
                if (
                    self.request.user.role.name == UserRole.MANAGER
                    and ACWBasePermission().has_api_permission(self.request)
                ):
                    managed_user_ids = self.request.user.managed_users.values_list(
                        "managed_user__id",
                        flat=True,
                    )

                    try:
                        query[query_field] += managed_user_ids
                    except KeyError:
                        pass

        return queryset.filter(**query)

    def finalize_response(self, request, response, *args, **kwargs):
        final_response = super().finalize_response(request, response, *args, **kwargs)

        if type(final_response.data) in [list, ReturnList]:
            final_response.data = {
                "results": super()
                .finalize_response(request, response, *args, **kwargs)
                .data
            }

        return final_response


class UserOwnedViewSet(BaseViewSet):
    def get_queryset(self):
        queryset = super().get_queryset()

        if self.request.user:
            if queryset.model is User:
                queryset = queryset.filter(id=self.request.user.id)

            elif hasattr(queryset.model, "user"):
                queryset = queryset.filter(user_id=self.request.user.id)

        return queryset

class BaseAPIListView(routers.APIRootView):
    """
    View returning a list of available APIs per app
    """

    http_method_names = ["get"]
    permission_classes = [IsInternal | IsAdmin]
