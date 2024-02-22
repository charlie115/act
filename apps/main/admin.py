from django.apps import apps
from django.contrib import admin
from django.contrib.sites.models import Site

from django_rq.admin import QueueAdmin
from django_rq.models import Queue
from unfold.admin import ModelAdmin


class CustomQueueAdmin(QueueAdmin, ModelAdmin):
    pass


apps.get_app_config("django_rq").verbose_name = "Redis Queue"


admin.site.unregister(Site)
admin.site.unregister(Queue)

admin.site.register(Queue, CustomQueueAdmin)
