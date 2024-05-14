from django.apps import apps
from django.contrib import admin
from django.contrib.sites.models import Site

from django_rq.admin import QueueAdmin
from django_rq.models import Queue
from unfold.admin import ModelAdmin

from django_celery_beat.admin import PeriodicTaskAdmin
from django_celery_beat.models import (
    ClockedSchedule,
    CrontabSchedule,
    IntervalSchedule,
    PeriodicTask,
    SolarSchedule,
)
from django_celery_results.admin import TaskResultAdmin
from django_celery_results.models import GroupResult, TaskResult


class UnfoldPeriodicTaskAdmin(ModelAdmin, PeriodicTaskAdmin):
    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class UnfoldTaskResultAdmin(ModelAdmin, TaskResultAdmin):
    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class UnfoldQueueAdmin(ModelAdmin, QueueAdmin):
    pass


apps.get_app_config("django_rq").verbose_name = "Redis Queue"


admin.site.unregister(Site)
admin.site.unregister(ClockedSchedule)
admin.site.unregister(CrontabSchedule)
admin.site.unregister(IntervalSchedule)
admin.site.unregister(PeriodicTask)
admin.site.unregister(SolarSchedule)
admin.site.unregister(GroupResult)
admin.site.unregister(TaskResult)
admin.site.unregister(Queue)

admin.site.register(PeriodicTask, UnfoldPeriodicTaskAdmin)
admin.site.register(TaskResult, UnfoldTaskResultAdmin)
admin.site.register(Queue, UnfoldQueueAdmin)
