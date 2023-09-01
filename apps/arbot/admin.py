from django.contrib import admin

from arbot.models import ArbotNode, ArbotUserConfig


admin.site.register(ArbotNode)
admin.site.register(ArbotUserConfig)
