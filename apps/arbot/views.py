from rest_framework import viewsets

from arbot.models import ArbotNode, ArbotUserConfig
from arbot.serializers import ArbotNodeSerializer, ArbotUserConfigSerializer


class ArbotNodeViewSet(viewsets.ModelViewSet):
    queryset = ArbotNode.objects.all().order_by("id")
    serializer_class = ArbotNodeSerializer


class ArbotUserConfigViewSet(viewsets.ModelViewSet):
    queryset = ArbotUserConfig.objects.all().order_by("id")
    serializer_class = ArbotUserConfigSerializer
