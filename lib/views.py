from django.db.models import Q
from rest_framework import routers, viewsets
from rest_framework.utils.serializer_helpers import ReturnList

from lib.permissions import IsAuthenticatedOwner, IsDjangoAdmin, IsACWAdmin, IsUser
from users.models import User


class BaseViewSet(viewsets.ModelViewSet):
    permission_classes = [IsUser | IsDjangoAdmin]

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
    permission_classes = [IsAuthenticatedOwner]

    def get_queryset(self):
        query = (
            Q(id=self.request.user.id)
            if self.queryset.model == User
            else Q(user=self.request.user)
        )
        return super(UserOwnedViewSet, self).get_queryset().filter(query)

    def perform_create(self, serializer):
        attrs = {}

        if self.queryset.model != User:
            attrs["user"] = self.request.user

        serializer.save(**attrs)


class UserOwned1To1ViewSet(UserOwnedViewSet):
    def get_permissions(self):
        # Since user:config is 1:1, create form must not be allowed when user already has config
        if (
            hasattr(self.request.user, "arbot_config")
            and self.request.user.arbot_config
        ):
            self.http_method_names = ["get", "put", "patch", "delete"]

        return [permission() for permission in self.permission_classes]


class UserOwnedOrManagerViewSet(UserOwnedViewSet):
    permission_classes = [IsAuthenticatedOwner | IsDjangoAdmin]

    def get_queryset(self):
        # For managers and admins, they should be able to view other users' resources
        # TODO: [ACW-54] Once management feature is to be implemented, update get_queryset() for managers/admins

        return self.queryset


class BaseEndpointListView(routers.APIRootView):
    """
    View returning a list of available endpoints per app
    """

    http_method_names = ["get"]
    permission_classes = [IsDjangoAdmin or IsACWAdmin]
