from django.contrib import admin
from .models import ExchangeServerStatus

@admin.register(ExchangeServerStatus)
class ExchangeServerStatusAdmin(admin.ModelAdmin):
    list_display = ['id', 'market_code', 'start_time', 'end_time', 'message', 'server_check']
    list_filter = ['market_code', 'start_time', 'end_time']
    search_fields = ['market_code__code', 'message']
    ordering = ['-start_time']
    date_hierarchy = 'start_time'

    # server_check is a property on the model, so we can show it as a readonly field
    readonly_fields = ['server_check']

    def server_check(self, obj):
        return obj.server_check
    server_check.boolean = True
    server_check.short_description = "Server Check Active?"

    fieldsets = (
        (None, {
            'fields': ('market_code', 'start_time', 'end_time', 'message', 'server_check')
        }),
    )