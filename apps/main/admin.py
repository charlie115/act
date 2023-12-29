from django.apps import apps
from django.contrib import admin
from django.contrib.sites.models import Site

from django_rq.admin import QueueAdmin
from django_rq.models import Queue
from unfold.admin import ModelAdmin


def get_app_list(self, request, app_label=None):
    """
    Return a sorted list of all the installed apps that have been
    registered in this site.
    """
    app_dict = self._build_app_dict(request, app_label)

    # Sort the apps
    app_order = [
        "authentication",
        "users",
        "socialaccounts",
        "tradecore",
        "infocore",
        "messagecore",
        "django_rq",
    ]
    app_order_dict = dict(zip(app_order, range(len(app_order))))

    app_list = sorted(
        app_dict.values(), key=lambda x: app_order_dict.get(x["app_label"], 0)
    )

    # Sort the models alphabetically within each app.
    for app in app_list:
        app["models"].sort(key=lambda x: x["name"])

    return app_list


class CustomQueueAdmin(QueueAdmin, ModelAdmin):
    pass


apps.get_app_config("django_rq").verbose_name = "Redis Queue"


admin.site.unregister(Site)
admin.site.unregister(Queue)

admin.site.register(Queue, CustomQueueAdmin)

admin.AdminSite.get_app_list = get_app_list
