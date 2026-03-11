import re
import uuid
import datetime

from django import forms
from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.urls import reverse, path
from django.utils.safestring import mark_safe
from django.template.response import TemplateResponse
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.utils.html import format_html
from django.db.models.query import QuerySet
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils.functional import cached_property

from unfold.admin import ModelAdmin, TabularInline
from unfold.widgets import SELECT_CLASSES
from urllib.parse import urljoin

from lib.status import HTTP_204_NO_CONTENT
from tradecore.models import (
    EnabledMarketCodeCombination,
    Node,
    TradeConfigAllocation,
    Trade,
    TradeLog,
    OrderHistory,
    TradeHistory,
    RepeatTrade,
)
from tradecore.views import TradeConfigViewSet, TradesViewSet
from users.models import User
from tradecore.mixins import TradeCoreMixin

class UsersInline(TabularInline):
    model = Node.users.through
    verbose_name = "User"

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class EnabledMarketCodeCombinationForm(forms.ModelForm):
    target = forms.ChoiceField(
        widget=forms.Select({"class": " ".join([*SELECT_CLASSES, "w-72"])}),
    )
    origin = forms.ChoiceField(
        widget=forms.Select({"class": " ".join([*SELECT_CLASSES, "w-72"])}),
    )

    class Meta:
        model = EnabledMarketCodeCombination
        fields = "__all__"


class EnabledMarketCodeCombinationAdmin(ModelAdmin):
    list_display = [
        "target",
        "origin",
        "trade_support",
    ]
    list_filter = [
        "target",
        "origin",
        "trade_support",
    ]
    search_fields = [
        "target",
        "origin",
        "trade_support",
    ]


class NodeAdmin(ModelAdmin):
    fields = [
        "name",
        "url",
        "description",
        "max_user_count",
        "market_code_combinations",
    ]
    list_display = ["name", "url", "description", "get_market_code_combinations"]
    search_fields = ["name", "url"]
    autocomplete_fields = ["market_code_combinations"]
    inlines = [
        UsersInline,
    ]

    def changelist_view(self, request, *args, **kwargs):
        self.request = request
        return super().changelist_view(request, *args, **kwargs)

    def get_market_code_combinations(self, obj):
        mobile_agent_regex = re.compile(
            r".*(iphone|mobile|androidtouch)", re.IGNORECASE
        )

        bg_color = {True: "green", False: "red"}
        trade_class = "px-2 py-1 rounded text-xxs bg-{bg_color}-100 text-{bg_color}-500 dark:bg-{bg_color}-500/20"

        new_line = ""
        market_code_combinations = []

        for market_code_combo in obj.market_code_combinations.all():
            if mobile_agent_regex.match(self.request.META["HTTP_USER_AGENT"]):
                new_line = "<br>"
                market_code_combinations.append(
                    f"{market_code_combo.target.code}:{market_code_combo.origin.code}<br>"
                    f"Trade Support={market_code_combo.trade_support}<br>"
                )
            else:
                market_code_combinations.append(
                    f"<p class='my-2'>{market_code_combo.target.code}:{market_code_combo.origin.code}&nbsp;&nbsp;"
                    f"<small class='{trade_class.format(bg_color=bg_color[market_code_combo.trade_support])}'>"
                    "Trade Support</small></p>"
                )

        return mark_safe(new_line.join(market_code_combinations))

    get_market_code_combinations.short_description = "Market Code Combinations"
    get_market_code_combinations.allow_tags = True


class TradeConfigAllocationAdmin(ModelAdmin):
    list_display = [
        "node",
        "target_market_code",
        "origin_market_code",
        "user",
        "trade_config_uuid",
        "delete_button",
    ]
    search_fields = [
        "node__name",
        "node__url",
        "target_market_code",
        "origin_market_code",
        "user__uuid",
        "user__email",
        "user__username",
        "user__first_name",
        "user__last_name",
        "trade_config_uuid",
    ]

    def delete_button(self, obj):
        delete_button_class = (
            "block border border-red-500 font-medium px-3 py-2 rounded-md text-center text-sm "
            "text-red-500 whitespace-nowrap dark:border-transparent dark:bg-red-500/20 dark:text-red-500"
        )
        url = urljoin(
            reverse(
                "admin:%s_%s_changelist" % (self.opts.app_label, self.opts.model_name),
                current_app=self.admin_site.name,
            ),
            f"{obj.id}/delete/",
        )
        return mark_safe(f'<a class="{delete_button_class}" href="{url}">Delete</a>')

    delete_button.short_description = "Delete?"

    def get_actions(self, request):
        """
        We need to allow has_delete_permissions to be able to delete a TradeConfigAllocation, but at the same time,
        remove bulk delete since we have to call trade_core api for each object we want to delete.
        """
        actions = super().get_actions(request)
        if "delete_selected" in actions:
            del actions["delete_selected"]
        return actions

    def delete_model(self, request, obj):
        api_response = TradeConfigViewSet().tradecore_destroy_api(
            url=obj.node.url,
            endpoint=TradeConfigViewSet.tradecore_api_endpoint,
            path_param=obj.trade_config_uuid,
        )

        if api_response.status_code == HTTP_204_NO_CONTENT:
            return super().delete_model(request, obj)

        try:
            message = api_response.json()
            message = message["detail"] if "detail" in message else message
        except Exception:
            message = api_response.content

        self.message_user(request, message, messages.ERROR)

    def response_delete(self, request, obj_display, obj_id):
        try:
            TradeConfigAllocation.objects.get(id=obj_id)
            url = reverse(
                "admin:%s_%s_changelist" % (self.opts.app_label, self.opts.model_name),
                current_app=self.admin_site.name,
            )
            return HttpResponseRedirect(url)

        except TradeConfigAllocation.DoesNotExist:
            return super().response_delete(request, obj_display, obj_id)

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

########################## Add a proper Django-compatible QuerySet for our API data
class TradeQuerySet:
    """A QuerySet-compatible class for API-backed data"""
    
    def __init__(self, data=None):
        # Store the raw data for our fake model
        self._result_cache = list(data or [])
        self._prefetch_related_lookups = []
        self.model = Trade
        
        # Add attributes to mimic Django QuerySet
        self.query = type('FakeQuery', (), {
            'order_by': [],
            'select_related': [],
            'distinct': False,
            'select': {},
            'where': None,
            'default_ordering': True,
            'used_aliases': set(),
            'combinator': None,
            'distinct_fields': [],
            'extra_select_mask': None,
            'select_for_update': False,
        })()
        
        # For compatibility with Django admin
        self._known_related_objects = {}  
        self._iterable_class = type('FakeIterable', (), {})
        self._fields = []
    
    def _clone(self):
        """Return a copy of the current QuerySet."""
        clone = TradeQuerySet(self._result_cache)
        # Copy needed attributes
        clone.query.order_by = list(self.query.order_by)
        return clone
    
    def __iter__(self):
        """Iterate over the results."""
        return iter(self._result_cache)
    
    def all(self):
        """Return all results."""
        return self._clone()
    
    def none(self):
        """Return an empty result set."""
        return TradeQuerySet([])
    
    def __len__(self):
        return len(self._result_cache)
    
    def __bool__(self):
        return bool(self._result_cache)
    
    def count(self):
        """Return the number of records."""
        return len(self._result_cache)
    
    def order_by(self, *field_names):
        """Order the results by the specified fields."""
        clone = self._clone()
        clone.query.order_by = field_names
        
        # Actually sort the results
        for field in reversed(field_names):
            reverse_order = False
            if field.startswith('-'):
                field = field[1:]
                reverse_order = True
            
            # Sort while handling None values
            clone._result_cache.sort(
                key=lambda obj: (getattr(obj, field, None) is None, getattr(obj, field, None)),
                reverse=reverse_order
            )
        
        return clone
    
    def filter(self, *args, **kwargs):
        """Filter the results."""
        clone = self._clone()
        filtered_results = []
        
        for obj in clone._result_cache:
            match = True
            for field, value in kwargs.items():
                # Handle simple field lookups
                if '__' in field:
                    field_name, lookup = field.split('__', 1)
                    obj_value = getattr(obj, field_name, None)
                    
                    if lookup == 'icontains' and isinstance(obj_value, str):
                        if not value.lower() in obj_value.lower():
                            match = False
                            break
                    elif lookup == 'contains' and isinstance(obj_value, str):
                        if not value in obj_value:
                            match = False
                            break
                    elif lookup == 'exact':
                        if obj_value != value:
                            match = False
                            break
                    elif lookup == 'in':
                        if obj_value not in value:
                            match = False
                            break
                else:
                    # Exact match
                    if getattr(obj, field, None) != value:
                        match = False
                        break
            
            if match:
                filtered_results.append(obj)
        
        clone._result_cache = filtered_results
        return clone
    
    def exclude(self, *args, **kwargs):
        """Exclude items matching the filter."""
        clone = self._clone()
        excluded_results = []
        
        for obj in clone._result_cache:
            exclude = False
            for field, value in kwargs.items():
                # Handle simple field lookups
                if '__' in field:
                    field_name, lookup = field.split('__', 1)
                    obj_value = getattr(obj, field_name, None)
                    
                    if lookup == 'icontains' and isinstance(obj_value, str):
                        if value.lower() in obj_value.lower():
                            exclude = True
                            break
                    elif lookup == 'contains' and isinstance(obj_value, str):
                        if value in obj_value:
                            exclude = True
                            break
                    elif lookup == 'exact':
                        if obj_value == value:
                            exclude = True
                            break
                    elif lookup == 'in':
                        if obj_value in value:
                            exclude = True
                            break
                else:
                    # Exact match
                    if getattr(obj, field, None) == value:
                        exclude = True
                        break
            
            if not exclude:
                excluded_results.append(obj)
        
        clone._result_cache = excluded_results
        return clone
    
    def get(self, *args, **kwargs):
        """Get a single object."""
        clone = self.filter(*args, **kwargs)
        if len(clone) == 1:
            return clone._result_cache[0]
        if not len(clone):
            from django.core.exceptions import ObjectDoesNotExist
            raise ObjectDoesNotExist(f"{self.model.__name__} matching query does not exist.")
        from django.core.exceptions import MultipleObjectsReturned
        raise MultipleObjectsReturned(f"get() returned more than one {self.model.__name__} -- it returned {len(clone)}!")
    
    def first(self):
        """Return the first object or None."""
        if len(self._result_cache) > 0:
            return self._result_cache[0]
        return None
    
    def last(self):
        """Return the last object or None."""
        if len(self._result_cache) > 0:
            return self._result_cache[-1]
        return None
    
    def values(self, *fields):
        """Return dictionaries of field values."""
        clone = self._clone()
        result = []
        
        for obj in clone._result_cache:
            item = {}
            for field in fields:
                item[field] = getattr(obj, field, None)
            result.append(item)
        
        clone._result_cache = result
        return clone
    
    def values_list(self, *fields, flat=False):
        """Return tuples of field values."""
        clone = self._clone()
        result = []
        
        if flat:
            if len(fields) > 1:
                raise TypeError("'flat' is not valid when values_list is called with more than one field.")
            field = fields[0]
            for obj in clone._result_cache:
                result.append(getattr(obj, field, None))
        else:
            for obj in clone._result_cache:
                item = []
                for field in fields:
                    item.append(getattr(obj, field, None))
                result.append(tuple(item))
        
        clone._result_cache = result
        return clone
    
    def distinct(self, *fields):
        """Return distinct objects."""
        clone = self._clone()
        
        # Very simple distinct implementation for compatibility
        if not fields:
            seen = set()
            result = []
            for obj in clone._result_cache:
                # Find an appropriate unique identifier based on model type
                if hasattr(obj, 'uuid'):
                    unique_id = obj.uuid
                elif hasattr(obj, 'order_id'):
                    unique_id = obj.order_id
                else:
                    # Fallback to using the object itself as its own identifier
                    unique_id = id(obj)
                    
                if unique_id not in seen:
                    seen.add(unique_id)
                    result.append(obj)
            clone._result_cache = result
        
        return clone
    
    def exists(self):
        """Check if any objects exist."""
        return bool(self._result_cache)
    
    @property
    def ordered(self):
        """Always return True for compatibility."""
        return True

    # Add this method to support slicing
    def __getitem__(self, key):
        """Support slicing the queryset with [start:stop] notation."""
        if isinstance(key, slice):
            # Handle slice objects (e.g., qs[5:10])
            clone = self._clone()
            clone._result_cache = self._result_cache[key]
            return clone
        elif isinstance(key, int):
            # Handle single index (e.g., qs[5])
            return self._result_cache[key]
        else:
            raise TypeError("QuerySet indices must be integers or slices")

#######################################
class TradeForm(forms.ModelForm):
    class Meta:
        model = Trade
        fields = [
            'usdt_conversion',
            'low',
            'high',
            'trigger_switch',
            'trade_switch',
            'trade_capital',
            'status',
            'remark',
        ]
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # You can customize form fields here if needed
        # For example, improving the usdt_conversion display
        if 'usdt_conversion' in self.fields:
            self.fields['usdt_conversion'].widget = forms.CheckboxInput()

class TradeAdmin(ModelAdmin):
    form = TradeForm
    
    list_display = [
        "uuid",
        "user_email",
        "trade_config_uuid", 
        "target_market_code",
        "origin_market_code",
        "registered_datetime", 
        "base_asset", 
        "usdt_conversion", 
        "display_low", 
        "display_high", 
        "display_trigger_switch", 
        "display_trade_switch", 
        "display_trade_capital", 
        "last_trade_history_uuid",
    ]
    search_fields = [
        "uuid",
        "trade_config_uuid",
        "registered_datetime",
        "base_asset",
        "usdt_conversion",
        "low",
        "high",
    ]
    list_filter = [
        "registered_datetime",
        "usdt_conversion",
        "low",
        "high",
        "status",
    ]
    
    readonly_fields = [
        'uuid',
        'base_asset',
        'trade_config_uuid',
        'registered_datetime',
        'last_trade_history_uuid',
    ]
    
    fieldsets = [
        ('Read-Only Information', {
            'fields': ['uuid', 'base_asset', 'trade_config_uuid','registered_datetime', 'last_trade_history_uuid']
        }),
        ('Trade Configuration', {
            'fields': ['usdt_conversion', 'low', 'high']
        }),
        ('Trade Controls', {
            'fields': ['trigger_switch', 'trade_switch', 'trade_capital']
        }),
        ('Status Information', {
            'fields': ['status', 'remark']
        }),
    ]
    
    def get_queryset(self, request):
        # Store the request for use in methods
        self.request = request
        
        # Get data from the trade_core API
        tradecore_mixin = TradeCoreMixin()

        # Get all nodes
        nodes = Node.objects.all()
        # if nodes is empty, return an empty QuerySet
        if not nodes:
            return TradeQuerySet()
            
        try:
            # Call the trade_core API directly
            total_trade_data = []
            for node in nodes:
                response = tradecore_mixin.tradecore_list_api(
                    url=node.url,
                    endpoint="trades/",
                    query_params={}  # You could add filter parameters here from request.GET
                )
            
                if response.status_code == 200:
                    trades_data = response.json()
                    total_trade_data.extend(trades_data)
                    
                # Convert API response to model instances
                trades = []
                for trade_data in total_trade_data:
                    # Create a new Trade instance
                    trade = Trade()
                    
                    # Set attributes with proper type conversion
                    try:
                        trade.uuid = uuid.UUID(trade_data.get('uuid')) if trade_data.get('uuid') else None
                        trade.trade_config_uuid = uuid.UUID(trade_data.get('trade_config_uuid')) if trade_data.get('trade_config_uuid') else None
                        trade.registered_datetime = trade_data.get('registered_datetime')
                        trade.base_asset = str(trade_data.get('base_asset'))
                        trade.usdt_conversion = bool(trade_data.get('usdt_conversion'))
                        trade.low = float(trade_data.get('low'))
                        trade.high = float(trade_data.get('high'))
                        trade.trigger_switch = trade_data.get('trigger_switch')
                        trade.trade_switch = trade_data.get('trade_switch')
                        trade.trade_capital = trade_data.get('trade_capital')
                        trade.last_trade_history_uuid = uuid.UUID(trade_data.get('last_trade_history_uuid')) if trade_data.get('last_trade_history_uuid') else None
                        trade.status = str(trade_data.get('status'))
                        trade.remark = str(trade_data.get('remark'))
                                                
                        trades.append(trade)
                    except (ValueError, TypeError) as e:
                        # Skip invalid trades
                        print(f"Error processing trade: {e}")
                
                # Create queryset from trades
                queryset = TradeQuerySet(trades)
                
                # Apply manual search if provided
                search_term = request.GET.get('q', '').strip()
                if search_term:
                    filtered_trades = []
                    for trade in queryset:
                        # Convert all searchable fields to strings for comparison
                        searchable_fields = [
                            str(getattr(trade, field, '')) for field in self.search_fields
                            if hasattr(trade, field) and getattr(trade, field) is not None
                        ]
                        
                        # Include the trade if any field contains the search term
                        if any(search_term.lower() in field.lower() for field in searchable_fields):
                            filtered_trades.append(trade)
                    
                    queryset = TradeQuerySet(filtered_trades)
                
                # After creating queryset and applying search, add this line before returning:
                queryset = queryset.order_by('-registered_datetime')
                
                return queryset
            else:
                # Log the error
                print(f"Error fetching trades: {response.status_code} - {response.content}")
                self.message_user(request, f"Error fetching trades: {response.status_code}", level=messages.ERROR)
                return TradeQuerySet()
                
        except Exception as e:
            # Handle errors gracefully
            print(f"Exception fetching trades: {str(e)}")
            self.message_user(request, f"Error fetching trades: {str(e)}", level=messages.ERROR)
            return TradeQuerySet()
    
    def user_email(self, obj):
        # Try to find the user related to this trade
        if hasattr(obj, 'trade_config_uuid') and obj.trade_config_uuid:
            user = User.objects.filter(trade_config_allocations__trade_config_uuid=obj.trade_config_uuid).first()
            if user:
                return user.email
        return "-"
    
    user_email.short_description = "User Email"
    
    def target_market_code(self, obj):
        """Get target market code from TradeConfigAllocation"""
        if hasattr(obj, 'trade_config_uuid') and obj.trade_config_uuid:
            trade_config = TradeConfigAllocation.objects.filter(
                trade_config_uuid=obj.trade_config_uuid
            ).first()
            if trade_config:
                return trade_config.target_market_code
        return "-"
    
    target_market_code.short_description = "Target Market"
    
    def origin_market_code(self, obj):
        """Get origin market code from TradeConfigAllocation"""
        if hasattr(obj, 'trade_config_uuid') and obj.trade_config_uuid:
            trade_config = TradeConfigAllocation.objects.filter(
                trade_config_uuid=obj.trade_config_uuid
            ).first()
            if trade_config:
                return trade_config.origin_market_code
        return "-"
    
    origin_market_code.short_description = "Origin Market"
    
    def has_add_permission(self, request, obj=None):
        return False
    
    def has_change_permission(self, request, obj=None):
        # Allow changes
        return True
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        extra_context = extra_context or {}
        # Enable the save buttons
        extra_context['show_save'] = True
        extra_context['show_save_and_continue'] = True
        extra_context['show_save_and_add_another'] = False
        return super().changeform_view(request, object_id, form_url, extra_context)
    
    def get_object(self, request, object_id, from_field=None):
        """Override get_object to fetch a single trade from the API"""
        tradecore_mixin = TradeCoreMixin()
        
        # Get all nodes - we need to find the correct node for this trade
        nodes = Node.objects.all()
        if not nodes:
            return None
            
        # Try to find the trade in all nodes
        for node in nodes:
            try:
                # Call the trade_core API for a single trade
                response = tradecore_mixin.tradecore_retrieve_api(
                    url=node.url,
                    endpoint="trades/",
                    path_param=object_id
                )
                
                if response.status_code == 200:
                    trade_data = response.json()
                    
                    # Create a Trade object from the API data
                    trade = Trade()
                    trade.uuid = uuid.UUID(trade_data.get('uuid')) if trade_data.get('uuid') else None
                    trade.trade_config_uuid = uuid.UUID(trade_data.get('trade_config_uuid')) if trade_data.get('trade_config_uuid') else None
                    trade.registered_datetime = trade_data.get('registered_datetime')
                    trade.base_asset = str(trade_data.get('base_asset'))
                    trade.usdt_conversion = bool(trade_data.get('usdt_conversion'))
                    trade.low = float(trade_data.get('low'))
                    trade.high = float(trade_data.get('high'))
                    trade.trigger_switch = trade_data.get('trigger_switch')
                    trade.trade_switch = trade_data.get('trade_switch')
                    trade.trade_capital = trade_data.get('trade_capital')
                    trade.last_trade_history_uuid = uuid.UUID(trade_data.get('last_trade_history_uuid')) if trade_data.get('last_trade_history_uuid') else None
                    trade.status = str(trade_data.get('status'))
                    trade.remark = str(trade_data.get('remark'))
                    
                    # Store the node for later use in save_model
                    trade.node = node
                    
                    return trade
                    
            except Exception as e:
                print(f"Exception fetching trade from node {node.name}: {str(e)}")
                
        return None
    
    def save_model(self, request, obj, form, change):
        """
        Override save_model to update the trade via the API
        """
        if not hasattr(obj, 'node'):
            # Try to find the trade's node
            trade_config_alloc = TradeConfigAllocation.objects.filter(
                trade_config_uuid=obj.trade_config_uuid
            ).first()
            
            if trade_config_alloc:
                node = trade_config_alloc.node
            else:
                # Fallback to the first node that has this trade
                for node in Node.objects.all():
                    response = TradeCoreMixin().tradecore_retrieve_api(
                        url=node.url,
                        endpoint="trades/",
                        path_param=str(obj.uuid)
                    )
                    if response.status_code == 200:
                        break
                else:
                    self.message_user(request, "Error: Could not find the node for this trade", level=messages.ERROR)
                    return
        else:
            node = obj.node
        
        # Prepare the data to update
        update_data = {
            'usdt_conversion': obj.usdt_conversion,
            'low': float(obj.low),
            'high': float(obj.high),
            'trigger_switch': obj.trigger_switch,
            'trade_switch': obj.trade_switch,
            'trade_capital': obj.trade_capital,
            'status': obj.status,
            'remark': obj.remark
        }
        
        try:
            # Call the API to update the trade
            response = TradeCoreMixin().tradecore_update_api(
                url=node.url,
                endpoint="trades/",
                path_param=str(obj.uuid),
                data=update_data
            )
            
            if response.status_code in [200, 201, 204]:
                self.message_user(request, "Trade was updated successfully.", level=messages.SUCCESS)
            else:
                # Try to get the error message from the response
                error_msg = f"Error updating trade: {response.status_code}"
                try:
                    error_data = response.json()
                    if 'detail' in error_data:
                        error_msg += f" - {error_data['detail']}"
                except:
                    error_msg += f" - {response.text}"
                
                self.message_user(request, error_msg, level=messages.ERROR)
                
        except Exception as e:
            self.message_user(
                request, 
                f"Error updating trade: {str(e)}", 
                level=messages.ERROR
            )

    # Add custom display methods for numeric fields
    def display_low(self, obj):
        return format_number(obj.low)
    display_low.short_description = "Low"
    
    def display_high(self, obj):
        return format_number(obj.high)
    display_high.short_description = "High"
    
    def display_trigger_switch(self, obj):
        return format_number(obj.trigger_switch)
    display_trigger_switch.short_description = "Trigger Switch"
    
    def display_trade_switch(self, obj):
        return format_number(obj.trade_switch)
    display_trade_switch.short_description = "Trade Switch"
    
    def display_trade_capital(self, obj):
        return format_number(obj.trade_capital)
    display_trade_capital.short_description = "Trade Capital"

class TradeLogQuerySet(TradeQuerySet):
    """Reuse the TradeQuerySet with TradeLog as model"""
    def __init__(self, data=None):
        super().__init__(data)
        self.model = TradeLog

class TradeLogForm(forms.ModelForm):
    class Meta:
        model = TradeLog
        fields = [
            'status',
            'remark',
        ]
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # You can customize form fields here if needed
        if 'usdt_conversion' in self.fields:
            self.fields['usdt_conversion'].widget = forms.CheckboxInput()

class TradeLogAdmin(ModelAdmin):
    form = TradeLogForm
    
    list_display = [
        "uuid",
        "trade_uuid",
        "user_email",
        "trade_config_uuid", 
        "target_market_code",
        "origin_market_code",
        "registered_datetime", 
        "base_asset", 
        "usdt_conversion", 
        "display_low", 
        "display_high", 
        "display_trade_capital", 
        "deleted",
        "status",
    ]
    search_fields = [
        "uuid",
        "trade_uuid",
        "trade_config_uuid",
        "base_asset",
        "status",
    ]
    list_filter = [
        "registered_datetime",
        "usdt_conversion",
        "deleted",
        "status",
    ]
    
    readonly_fields = [
        'uuid',
        'trade_uuid',
        'trade_config_uuid',
        'registered_datetime',
        'base_asset',
        'usdt_conversion',
        'low',
        'high',
        'trade_capital',
        'deleted',
    ]
    
    def get_queryset(self, request):
        # Store the request for use in methods
        self.request = request
        
        # Get data from the trade_core API
        tradecore_mixin = TradeCoreMixin()

        # Get all nodes
        nodes = Node.objects.all()
        # if nodes is empty, return an empty QuerySet
        if not nodes:
            return TradeLogQuerySet()
            
        try:
            # Call the trade_core API directly
            total_tradelog_data = []
            for node in nodes:
                response = tradecore_mixin.tradecore_list_api(
                    url=node.url,
                    endpoint="trade-log/",
                    query_params={}  # You could add filter parameters here from request.GET
                )
            
                if response.status_code == 200:
                    tradelog_data = response.json()
                    total_tradelog_data.extend(tradelog_data)
                    
                # Convert API response to model instances
                tradelogs = []
                for log_data in total_tradelog_data:
                    # Create a new TradeLog instance
                    tradelog = TradeLog()
                    
                    # Set attributes with proper type conversion
                    try:
                        tradelog.uuid = uuid.UUID(log_data.get('uuid')) if log_data.get('uuid') else None
                        tradelog.trade_uuid = uuid.UUID(log_data.get('trade_uuid')) if log_data.get('trade_uuid') else None
                        tradelog.trade_config_uuid = uuid.UUID(log_data.get('trade_config_uuid')) if log_data.get('trade_config_uuid') else None
                        tradelog.registered_datetime = log_data.get('registered_datetime')
                        tradelog.base_asset = str(log_data.get('base_asset', ''))
                        tradelog.usdt_conversion = bool(log_data.get('usdt_conversion'))
                        tradelog.low = float(log_data.get('low', 0))
                        tradelog.high = float(log_data.get('high', 0))
                        tradelog.trade_capital = log_data.get('trade_capital')
                        tradelog.deleted = bool(log_data.get('deleted', False))
                        tradelog.status = str(log_data.get('status', ''))
                        tradelog.remark = str(log_data.get('remark', ''))
                                                    
                        tradelogs.append(tradelog)
                    except (ValueError, TypeError) as e:
                        # Skip invalid tradelogs
                        print(f"Error processing trade log: {e}")
                
                # Apply search if provided
                queryset = TradeLogQuerySet(tradelogs)
                
                # Manual search implementation
                search_term = request.GET.get('q', '').strip()
                if search_term:
                    filtered_logs = []
                    for log in queryset:
                        # Convert all searchable fields to strings for comparison
                        searchable_fields = [
                            str(getattr(log, field, '')) for field in self.search_fields
                            if hasattr(log, field) and getattr(log, field) is not None
                        ]
                        
                        # Include the log if any field contains the search term
                        if any(search_term.lower() in field.lower() for field in searchable_fields):
                            filtered_logs.append(log)
                    
                    queryset = TradeLogQuerySet(filtered_logs)
                
                # After creating queryset and applying search, add this line before returning:
                queryset = queryset.order_by('-registered_datetime')
                
                return queryset
            else:
                # Log the error
                print(f"Error fetching trade logs: {response.status_code} - {response.content}")
                self.message_user(request, f"Error fetching trade logs: {response.status_code}", level=messages.ERROR)
                return TradeLogQuerySet()
                
        except Exception as e:
            # Handle errors gracefully
            print(f"Exception fetching trade logs: {str(e)}")
            self.message_user(request, f"Error fetching trade logs: {str(e)}", level=messages.ERROR)
            return TradeLogQuerySet()
    
    def user_email(self, obj):
        # Try to find the user related to this trade log
        if hasattr(obj, 'trade_config_uuid') and obj.trade_config_uuid:
            user = User.objects.filter(trade_config_allocations__trade_config_uuid=obj.trade_config_uuid).first()
            if user:
                return user.email
        return "-"
    
    user_email.short_description = "User Email"
    
    def target_market_code(self, obj):
        """Get target market code from TradeConfigAllocation"""
        if hasattr(obj, 'trade_config_uuid') and obj.trade_config_uuid:
            trade_config = TradeConfigAllocation.objects.filter(
                trade_config_uuid=obj.trade_config_uuid
            ).first()
            if trade_config:
                return trade_config.target_market_code
        return "-"
    
    target_market_code.short_description = "Target Market"
    
    def origin_market_code(self, obj):
        """Get origin market code from TradeConfigAllocation"""
        if hasattr(obj, 'trade_config_uuid') and obj.trade_config_uuid:
            trade_config = TradeConfigAllocation.objects.filter(
                trade_config_uuid=obj.trade_config_uuid
            ).first()
            if trade_config:
                return trade_config.origin_market_code
        return "-"
    
    origin_market_code.short_description = "Origin Market"
    
    def has_add_permission(self, request, obj=None):
        return False
    
    def has_change_permission(self, request, obj=None):
        # Disable editing completely
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    # Disable access to the change form (detail view)
    def has_view_permission(self, request, obj=None):
        # Only allow listing, not viewing details
        if request.path.endswith('/change/'):
            return False
        return True
    
    # Override change_view to redirect back to list view
    def change_view(self, request, object_id, form_url='', extra_context=None):
        # Redirect to the list view instead of showing the detail form
        return HttpResponseRedirect(reverse('admin:tradecore_tradelog_changelist'))

    # Add custom display methods for numeric fields
    def display_low(self, obj):
        return format_number(obj.low)
    display_low.short_description = "Low"
    
    def display_high(self, obj):
        return format_number(obj.high)
    display_high.short_description = "High"
    
    def display_trade_capital(self, obj):
        return format_number(obj.trade_capital)
    display_trade_capital.short_description = "Trade Capital"
    
class RepeatTradeQuerySet(TradeQuerySet):
    """Reuse the TradeQuerySet with RepeatTrade as model"""
    def __init__(self, data=None):
        super().__init__(data)
        self.model = RepeatTrade

class RepeatTradeForm(forms.ModelForm):
    class Meta:
        model = RepeatTrade
        fields = [
            'kline_interval',
            'kline_num',
            'pauto_num',
            'auto_repeat_switch',
            'auto_repeat_num',
            'status',
            'remark',
        ]
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # You can customize form fields here if needed

class RepeatTradeAdmin(ModelAdmin):
    form = RepeatTradeForm
    
    list_display = [
        "uuid",
        "user_email",
        "trade_uuid",
        "registered_datetime",
        "last_updated_datetime",
        "kline_interval",
        "display_kline_num",
        "display_pauto_num",
        "display_auto_repeat_switch",
        "display_auto_repeat_num",
        "status",
    ]
    search_fields = [
        "uuid",
        "trade_uuid",
        "registered_datetime",
        "kline_interval",
        "status",
    ]
    list_filter = [
        "registered_datetime",
        "kline_interval",
        "status",
    ]
    
    readonly_fields = [
        'uuid',
        'trade_uuid',
        'registered_datetime',
        'last_updated_datetime',
    ]
    
    fieldsets = [
        ('Read-Only Information', {
            'fields': ['uuid', 'trade_uuid', 'registered_datetime', 'last_updated_datetime']
        }),
        ('Repeat Trade Configuration', {
            'fields': ['kline_interval', 'kline_num', 'pauto_num', 'auto_repeat_switch', 'auto_repeat_num']
        }),
        ('Status Information', {
            'fields': ['status', 'remark']
        }),
    ]
    
    def get_queryset(self, request):
        # Store the request for use in methods
        self.request = request
        
        # Get data from the trade_core API
        tradecore_mixin = TradeCoreMixin()

        # Get all nodes
        nodes = Node.objects.all()
        # if nodes is empty, return an empty QuerySet
        if not nodes:
            return RepeatTradeQuerySet()
            
        try:
            # Call the trade_core API directly
            total_repeat_trade_data = []
            for node in nodes:
                response = tradecore_mixin.tradecore_list_api(
                    url=node.url,
                    endpoint="repeat-trades/",
                    query_params={}  # You could add filter parameters here from request.GET
                )
            
                if response.status_code == 200:
                    repeat_trades_data = response.json()
                    total_repeat_trade_data.extend(repeat_trades_data)
                    
                # Convert API response to model instances
                repeat_trades = []
                for repeat_trade_data in total_repeat_trade_data:
                    # Create a new RepeatTrade instance
                    repeat_trade = RepeatTrade()
                    
                    # Set attributes with proper type conversion
                    try:
                        repeat_trade.uuid = uuid.UUID(repeat_trade_data.get('uuid')) if repeat_trade_data.get('uuid') else None
                        repeat_trade.trade_uuid = uuid.UUID(repeat_trade_data.get('trade_uuid')) if repeat_trade_data.get('trade_uuid') else None
                        repeat_trade.registered_datetime = repeat_trade_data.get('registered_datetime')
                        repeat_trade.last_updated_datetime = repeat_trade_data.get('last_updated_datetime')
                        repeat_trade.kline_interval = str(repeat_trade_data.get('kline_interval', ''))
                        repeat_trade.kline_num = int(repeat_trade_data.get('kline_num', 0)) if repeat_trade_data.get('kline_num') is not None else None
                        repeat_trade.pauto_num = float(repeat_trade_data.get('pauto_num', 0)) if repeat_trade_data.get('pauto_num') is not None else None
                        repeat_trade.auto_repeat_switch = int(repeat_trade_data.get('auto_repeat_switch', 0)) if repeat_trade_data.get('auto_repeat_switch') is not None else None
                        repeat_trade.auto_repeat_num = int(repeat_trade_data.get('auto_repeat_num', 0)) if repeat_trade_data.get('auto_repeat_num') is not None else None
                        repeat_trade.status = str(repeat_trade_data.get('status', ''))
                        repeat_trade.remark = str(repeat_trade_data.get('remark', ''))
                                                
                        repeat_trades.append(repeat_trade)
                    except (ValueError, TypeError) as e:
                        # Skip invalid trades
                        print(f"Error processing repeat trade: {e}")
                
                # Create queryset from repeat trades
                queryset = RepeatTradeQuerySet(repeat_trades)
                
                # Apply manual search if provided
                search_term = request.GET.get('q', '').strip()
                if search_term:
                    filtered_repeat_trades = []
                    for repeat_trade in queryset:
                        # Convert all searchable fields to strings for comparison
                        searchable_fields = [
                            str(getattr(repeat_trade, field, '')) for field in self.search_fields
                            if hasattr(repeat_trade, field) and getattr(repeat_trade, field) is not None
                        ]
                        
                        # Include the repeat trade if any field contains the search term
                        if any(search_term.lower() in field.lower() for field in searchable_fields):
                            filtered_repeat_trades.append(repeat_trade)
                    
                    queryset = RepeatTradeQuerySet(filtered_repeat_trades)
                
                # After creating queryset and applying search, add this line before returning:
                queryset = queryset.order_by('-registered_datetime')
                
                return queryset
            else:
                # Log the error
                print(f"Error fetching repeat trades: {response.status_code} - {response.content}")
                self.message_user(request, f"Error fetching repeat trades: {response.status_code}", level=messages.ERROR)
                return RepeatTradeQuerySet()
                
        except Exception as e:
            # Handle errors gracefully
            print(f"Exception fetching repeat trades: {str(e)}")
            self.message_user(request, f"Error fetching repeat trades: {str(e)}", level=messages.ERROR)
            return RepeatTradeQuerySet()
    
    def user_email(self, obj):
        # Try to find the user related to this trade
        if hasattr(obj, 'trade_uuid') and obj.trade_uuid:
            # First try to get the trade record
            trade = None
            nodes = Node.objects.all()
            tradecore_mixin = TradeCoreMixin()
            
            for node in nodes:
                response = tradecore_mixin.tradecore_retrieve_api(
                    url=node.url,
                    endpoint="trades/",
                    path_param=str(obj.trade_uuid)
                )
                if response.status_code == 200:
                    trade_data = response.json()
                    if 'trade_config_uuid' in trade_data:
                        # Now get the user from the trade config
                        user = User.objects.filter(trade_config_allocations__trade_config_uuid=trade_data['trade_config_uuid']).first()
                        if user:
                            return user.email
            return "-"
        return "-"
    
    user_email.short_description = "User Email"
    
    def get_object(self, request, object_id, from_field=None):
        """Override get_object to fetch a single repeat trade from the API"""
        tradecore_mixin = TradeCoreMixin()
        
        # Get all nodes - we need to find the correct node for this repeat trade
        nodes = Node.objects.all()
        if not nodes:
            return None
            
        # Try to find the repeat trade in all nodes
        for node in nodes:
            try:
                # Call the trade_core API for a single repeat trade
                response = tradecore_mixin.tradecore_retrieve_api(
                    url=node.url,
                    endpoint="repeat-trades/",
                    path_param=object_id
                )
                
                if response.status_code == 200:
                    repeat_trade_data = response.json()
                    
                    # Create a RepeatTrade object from the API data
                    repeat_trade = RepeatTrade()
                    repeat_trade.uuid = uuid.UUID(repeat_trade_data.get('uuid')) if repeat_trade_data.get('uuid') else None
                    repeat_trade.trade_uuid = uuid.UUID(repeat_trade_data.get('trade_uuid')) if repeat_trade_data.get('trade_uuid') else None
                    repeat_trade.registered_datetime = repeat_trade_data.get('registered_datetime')
                    repeat_trade.last_updated_datetime = repeat_trade_data.get('last_updated_datetime')
                    repeat_trade.kline_interval = str(repeat_trade_data.get('kline_interval', ''))
                    repeat_trade.kline_num = int(repeat_trade_data.get('kline_num', 0)) if repeat_trade_data.get('kline_num') is not None else None
                    repeat_trade.pauto_num = float(repeat_trade_data.get('pauto_num', 0)) if repeat_trade_data.get('pauto_num') is not None else None
                    repeat_trade.auto_repeat_switch = int(repeat_trade_data.get('auto_repeat_switch', 0)) if repeat_trade_data.get('auto_repeat_switch') is not None else None
                    repeat_trade.auto_repeat_num = int(repeat_trade_data.get('auto_repeat_num', 0)) if repeat_trade_data.get('auto_repeat_num') is not None else None
                    repeat_trade.status = str(repeat_trade_data.get('status', ''))
                    repeat_trade.remark = str(repeat_trade_data.get('remark', ''))
                    
                    # Store the node for later use in save_model
                    repeat_trade.node = node
                    # Store the trade_uuid for later use in save_model
                    repeat_trade._trade_uuid = repeat_trade.trade_uuid
                    
                    return repeat_trade
                    
            except Exception as e:
                print(f"Exception fetching repeat trade from node {node.name}: {str(e)}")
                
        return None
    
    def save_model(self, request, obj, form, change):
        """
        Override save_model to update the repeat trade via the API
        """
        if not hasattr(obj, 'node'):
            # Try to find a node that contains this repeat trade
            for node in Node.objects.all():
                response = TradeCoreMixin().tradecore_retrieve_api(
                    url=node.url,
                    endpoint="repeat-trades/",
                    path_param=str(obj.uuid)
                )
                if response.status_code == 200:
                    obj.node = node
                    break
            else:
                self.message_user(request, "Error: Could not find the node for this repeat trade", level=messages.ERROR)
                return
        
        # Prepare the data to update
        update_data = {
            'kline_interval': obj.kline_interval,
            'kline_num': obj.kline_num,
            'pauto_num': float(obj.pauto_num) if obj.pauto_num is not None else None,
            'auto_repeat_switch': obj.auto_repeat_switch,
            'auto_repeat_num': obj.auto_repeat_num,
            'status': obj.status,
            'remark': obj.remark
        }
        
        try:
            # Call the API to update the repeat trade
            response = TradeCoreMixin().tradecore_update_api(
                url=obj.node.url,
                endpoint="repeat-trades/",
                path_param=str(obj.uuid),
                data=update_data
            )
            
            if response.status_code in [200, 201, 204]:
                self.message_user(request, "Repeat Trade was updated successfully.", level=messages.SUCCESS)
            else:
                # Try to get the error message from the response
                error_msg = f"Error updating repeat trade: {response.status_code}"
                try:
                    error_data = response.json()
                    if 'detail' in error_data:
                        error_msg += f" - {error_data['detail']}"
                except:
                    error_msg += f" - {response.text}"
                
                self.message_user(request, error_msg, level=messages.ERROR)
                
        except Exception as e:
            self.message_user(
                request, 
                f"Error updating repeat trade: {str(e)}", 
                level=messages.ERROR
            )

    # Add custom display methods for numeric fields
    def display_kline_num(self, obj):
        return format_number(obj.kline_num)
    display_kline_num.short_description = "Kline Number"
    
    def display_pauto_num(self, obj):
        return format_number(obj.pauto_num)
    display_pauto_num.short_description = "P-Auto Number"
    
    def display_auto_repeat_switch(self, obj):
        return format_number(obj.auto_repeat_switch)
    display_auto_repeat_switch.short_description = "Auto Repeat Switch"
    
    def display_auto_repeat_num(self, obj):
        return format_number(obj.auto_repeat_num)
    display_auto_repeat_num.short_description = "Auto Repeat Number"

class OrderHistoryQuerySet(TradeQuerySet):
    """Reuse the TradeQuerySet with OrderHistory as model"""
    def __init__(self, data=None):
        super().__init__(data)
        self.model = OrderHistory
    
    def distinct(self, *fields):
        """Return distinct objects using order_id instead of uuid."""
        clone = self._clone()
        
        # Very simple distinct implementation for compatibility
        if not fields:
            seen = set()
            result = []
            for obj in clone._result_cache:
                if obj.order_id not in seen:
                    seen.add(obj.order_id)
                    result.append(obj)
            clone._result_cache = result
        
        return clone

class OrderHistoryAdmin(ModelAdmin):
    list_display = [
        "order_id",
        "user_email",
        "trade_config_uuid",
        "trade_uuid",
        "registered_datetime",
        "order_type",
        "market_code",
        "symbol",
        "quote_asset",
        "side",
        "display_price",
        "display_qty",
        "display_fee",
    ]
    search_fields = [
        "order_id",
        "trade_config_uuid",
        "trade_uuid",
        "market_code",
        "symbol",
        "side",
    ]
    list_filter = [
        "registered_datetime",
        "order_type",
        "market_code",
        "side",
    ]
    
    def get_queryset(self, request):
        # Store the request for use in methods
        self.request = request
        
        # Get data from the trade_core API
        tradecore_mixin = TradeCoreMixin()

        # Get all nodes
        nodes = Node.objects.all()
        # if nodes is empty, return an empty QuerySet
        if not nodes:
            return OrderHistoryQuerySet()
            
        try:
            # Call the trade_core API directly
            total_order_data = []
            for node in nodes:
                response = tradecore_mixin.tradecore_list_api(
                    url=node.url,
                    endpoint="order-history/",
                    query_params={}  # You could add filter parameters here from request.GET
                )
            
                if response.status_code == 200:
                    order_data = response.json()
                    total_order_data.extend(order_data)
                    
                # Convert API response to model instances
                orders = []
                for order_item in total_order_data:
                    # Create a new OrderHistory instance
                    order = OrderHistory()
                    
                    # Set attributes with proper type conversion
                    try:
                        order.id = int(order_item.get('id', 0))
                        order.order_id = str(order_item.get('order_id', ''))
                        order.trade_config_uuid = uuid.UUID(order_item.get('trade_config_uuid')) if order_item.get('trade_config_uuid') else None
                        order.trade_uuid = uuid.UUID(order_item.get('trade_uuid')) if order_item.get('trade_uuid') else None
                        order.registered_datetime = order_item.get('registered_datetime')
                        order.order_type = str(order_item.get('order_type', ''))
                        order.market_code = str(order_item.get('market_code', ''))
                        order.symbol = str(order_item.get('symbol', ''))
                        order.quote_asset = str(order_item.get('quote_asset', ''))
                        order.side = str(order_item.get('side', ''))
                        order.price = float(order_item.get('price', 0))
                        order.qty = float(order_item.get('qty', 0))
                        order.fee = float(order_item.get('fee', 0))
                        order.remark = str(order_item.get('remark', ''))
                                                    
                        orders.append(order)
                    except (ValueError, TypeError) as e:
                        # Skip invalid orders
                        print(f"Error processing order history: {e}")
                
                # Apply search if provided
                queryset = OrderHistoryQuerySet(orders)
                
                # Manual search implementation
                search_term = request.GET.get('q', '').strip()
                if search_term:
                    filtered_orders = []
                    for order in queryset:
                        # Convert all searchable fields to strings for comparison
                        searchable_fields = [
                            str(getattr(order, field, '')) for field in self.search_fields
                            if hasattr(order, field) and getattr(order, field) is not None
                        ]
                        
                        # Include the order if any field contains the search term
                        if any(search_term.lower() in field.lower() for field in searchable_fields):
                            filtered_orders.append(order)
                    
                    queryset = OrderHistoryQuerySet(filtered_orders)
                
                # After creating queryset and applying search, add this line before returning:
                queryset = queryset.order_by('-registered_datetime')
                
                return queryset
            else:
                # Log the error
                print(f"Error fetching order history: {response.status_code} - {response.content}")
                self.message_user(request, f"Error fetching order history: {response.status_code}", level=messages.ERROR)
                return OrderHistoryQuerySet()
                
        except Exception as e:
            # Handle errors gracefully
            print(f"Exception fetching order history: {str(e)}")
            self.message_user(request, f"Error fetching order history: {str(e)}", level=messages.ERROR)
            return OrderHistoryQuerySet()
    
    def user_email(self, obj):
        """Get user email from TradeConfigAllocation"""
        if hasattr(obj, 'trade_config_uuid') and obj.trade_config_uuid:
            user = User.objects.filter(trade_config_allocations__trade_config_uuid=obj.trade_config_uuid).first()
            if user:
                return user.email
        return "-"
    
    user_email.short_description = "User Email"
    
    def has_add_permission(self, request, obj=None):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    # Disable access to the change form (detail view)
    def has_view_permission(self, request, obj=None):
        # Only allow listing, not viewing details
        if request.path.endswith('/change/'):
            return False
        return True
    
    # Override change_view to redirect back to list view
    def change_view(self, request, object_id, form_url='', extra_context=None):
        # Redirect to the list view instead of showing the detail form
        return HttpResponseRedirect(reverse('admin:tradecore_orderhistory_changelist'))

    # Add custom display methods for numeric fields
    def display_price(self, obj):
        return format_number(obj.price)
    display_price.short_description = "Price"
    
    def display_qty(self, obj):
        return format_number(obj.qty)
    display_qty.short_description = "Quantity"
    
    def display_fee(self, obj):
        return format_number(obj.fee)
    display_fee.short_description = "Fee"

class TradeHistoryQuerySet(TradeQuerySet):
    """Reuse the TradeQuerySet with TradeHistory as model"""
    def __init__(self, data=None):
        super().__init__(data)
        self.model = TradeHistory
    
    def distinct(self, *fields):
        """Return distinct objects using uuid instead of order_id."""
        clone = self._clone()
        
        # Very simple distinct implementation for compatibility
        if not fields:
            seen = set()
            result = []
            for obj in clone._result_cache:
                if obj.uuid not in seen:
                    seen.add(obj.uuid)
                    result.append(obj)
            clone._result_cache = result
        
        return clone

class TradeHistoryAdmin(ModelAdmin):
    list_display = [
        "uuid",
        "user_email",
        "trade_config_uuid",
        "trade_uuid",
        "registered_datetime",
        "trade_side",
        "base_asset",
        "target_order_id",
        "origin_order_id",
        "display_target_premium_value",
        "display_executed_premium_value",
        "display_slippage_p",
        "display_dollar",
    ]
    search_fields = [
        "uuid",
        "trade_config_uuid",
        "trade_uuid",
        "trade_side",
        "base_asset",
        "target_order_id",
        "origin_order_id",
    ]
    list_filter = [
        "registered_datetime",
        "trade_side",
        "base_asset",
    ]
    
    def get_queryset(self, request):
        # Store the request for use in methods
        self.request = request
        
        # Get data from the trade_core API
        tradecore_mixin = TradeCoreMixin()

        # Get all nodes
        nodes = Node.objects.all()
        # if nodes is empty, return an empty QuerySet
        if not nodes:
            return TradeHistoryQuerySet()
            
        try:
            # Call the trade_core API directly
            total_history_data = []
            for node in nodes:
                response = tradecore_mixin.tradecore_list_api(
                    url=node.url,
                    endpoint="trade-history/",
                    query_params={}  # You could add filter parameters here from request.GET
                )
            
                if response.status_code == 200:
                    history_data = response.json()
                    total_history_data.extend(history_data)
                    
                # Convert API response to model instances
                histories = []
                for history_item in total_history_data:
                    # Create a new TradeHistory instance
                    history = TradeHistory()
                    
                    # Set attributes with proper type conversion
                    try:
                        history.uuid = uuid.UUID(history_item.get('uuid')) if history_item.get('uuid') else None
                        history.trade_config_uuid = uuid.UUID(history_item.get('trade_config_uuid')) if history_item.get('trade_config_uuid') else None
                        history.trade_uuid = uuid.UUID(history_item.get('trade_uuid')) if history_item.get('trade_uuid') else None
                        history.registered_datetime = history_item.get('registered_datetime')
                        history.trade_side = str(history_item.get('trade_side', ''))
                        history.base_asset = str(history_item.get('base_asset', ''))
                        history.target_order_id = str(history_item.get('target_order_id', ''))
                        history.origin_order_id = str(history_item.get('origin_order_id', ''))
                        history.target_premium_value = float(history_item.get('target_premium_value', 0))
                        history.executed_premium_value = float(history_item.get('executed_premium_value', 0))
                        history.slippage_p = float(history_item.get('slippage_p', 0))
                        history.dollar = float(history_item.get('dollar', 0))
                        history.remark = str(history_item.get('remark', ''))
                                                    
                        histories.append(history)
                    except (ValueError, TypeError) as e:
                        # Skip invalid history items
                        print(f"Error processing trade history: {e}")
                
                # Apply search if provided
                queryset = TradeHistoryQuerySet(histories)
                
                # Manual search implementation
                search_term = request.GET.get('q', '').strip()
                if search_term:
                    filtered_histories = []
                    for history in queryset:
                        # Convert all searchable fields to strings for comparison
                        searchable_fields = [
                            str(getattr(history, field, '')) for field in self.search_fields
                            if hasattr(history, field) and getattr(history, field) is not None
                        ]
                        
                        # Include the history if any field contains the search term
                        if any(search_term.lower() in field.lower() for field in searchable_fields):
                            filtered_histories.append(history)
                    
                    queryset = TradeHistoryQuerySet(filtered_histories)
                
                # After creating queryset and applying search, add this line before returning:
                queryset = queryset.order_by('-registered_datetime')
                
                return queryset
            else:
                # Log the error
                print(f"Error fetching trade history: {response.status_code} - {response.content}")
                self.message_user(request, f"Error fetching trade history: {response.status_code}", level=messages.ERROR)
                return TradeHistoryQuerySet()
                
        except Exception as e:
            # Handle errors gracefully
            print(f"Exception fetching trade history: {str(e)}")
            self.message_user(request, f"Error fetching trade history: {str(e)}", level=messages.ERROR)
            return TradeHistoryQuerySet()
    
    def user_email(self, obj):
        """Get user email from TradeConfigAllocation"""
        if hasattr(obj, 'trade_config_uuid') and obj.trade_config_uuid:
            user = User.objects.filter(trade_config_allocations__trade_config_uuid=obj.trade_config_uuid).first()
            if user:
                return user.email
        return "-"
    
    user_email.short_description = "User Email"
    
    # Add custom display methods for numeric fields
    def display_target_premium_value(self, obj):
        return format_number(obj.target_premium_value)
    display_target_premium_value.short_description = "Target Premium Value"
    
    def display_executed_premium_value(self, obj):
        return format_number(obj.executed_premium_value)
    display_executed_premium_value.short_description = "Executed Premium Value"
    
    def display_slippage_p(self, obj):
        return format_number(obj.slippage_p)
    display_slippage_p.short_description = "Slippage %"
    
    def display_dollar(self, obj):
        return format_number(obj.dollar)
    display_dollar.short_description = "Dollar"
    
    def has_add_permission(self, request, obj=None):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    # Disable access to the change form (detail view)
    def has_view_permission(self, request, obj=None):
        # Only allow listing, not viewing details
        if request.path.endswith('/change/'):
            return False
        return True
    
    # Override change_view to redirect back to list view
    def change_view(self, request, object_id, form_url='', extra_context=None):
        # Redirect to the list view instead of showing the detail form
        return HttpResponseRedirect(reverse('admin:tradecore_tradehistory_changelist'))

# Register the TradeHistory model with the admin site
admin.site.register(TradeHistory, TradeHistoryAdmin)
admin.site.register(EnabledMarketCodeCombination, EnabledMarketCodeCombinationAdmin)
admin.site.register(Node, NodeAdmin)
admin.site.register(TradeConfigAllocation, TradeConfigAllocationAdmin)
admin.site.register(Trade, TradeAdmin)
admin.site.register(TradeLog, TradeLogAdmin)
admin.site.register(RepeatTrade, RepeatTradeAdmin)
admin.site.register(OrderHistory, OrderHistoryAdmin)

def format_number(value):
    """Format a number to remove trailing zeros"""
    if value is None:
        return "-"
    
    # Convert to float first to ensure we're working with a number
    try:
        value = float(value)
        # Convert to string and remove trailing zeros
        s = str(value)
        return s.rstrip('0').rstrip('.') if '.' in s else s
    except (ValueError, TypeError):
        return str(value)
