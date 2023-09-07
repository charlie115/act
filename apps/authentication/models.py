from django.contrib.auth.models import Group

from rest_framework.authtoken.models import Token


class ProxyGroup(Group):
    class Meta:
        proxy = True
        verbose_name = "Group"


class ProxyToken(Token):
    class Meta:
        proxy = True
        verbose_name = "Token"
