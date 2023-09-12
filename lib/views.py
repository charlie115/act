from rest_framework import routers, viewsets

from lib.permissions import IsDjangoAdmin, IsACWAdmin, IsUser


class BaseViewSet(viewsets.ModelViewSet):
    permission_classes = [IsUser]


class BaseEndpointListView(routers.APIRootView):
    """
    View returning a list of available endpoints per app
    """

    http_method_names = ["get"]
    permission_classes = [IsDjangoAdmin or IsACWAdmin]
