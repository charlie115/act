from rest_framework import viewsets
from users.models import User, UserFavoriteSymbols, UserProfile
from users.serializers import (
    UserSerializer,
    UserFavoriteSymbolsSerializer,
    UserProfileSerializer,
)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by("id")
    serializer_class = UserSerializer


class UserFavoriteSymbolsViewSet(viewsets.ModelViewSet):
    queryset = UserFavoriteSymbols.objects.all().order_by("id")
    serializer_class = UserFavoriteSymbolsSerializer


class UserProfileViewSet(viewsets.ModelViewSet):
    queryset = UserProfile.objects.all().order_by("id")
    serializer_class = UserProfileSerializer
    http_method_names = ["get", "put", "patch", "delete"]
