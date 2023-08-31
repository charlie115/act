import importlib
import os

from django.apps import apps
from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from rest_framework import response, routers


class EndpointListView(routers.APIRootView):
    """
    List of all endpoints
    """
    http_method_names = ['get']

    def get(self, request, *args, **kwargs):
        api_list = {
            'admin': request.build_absolute_uri('admin/'),
        }

        for name, app in apps.app_configs.items():
            if name in settings.LOCAL_APPS:
                if importlib.util.find_spec(f'apps.{name}.urls'):
                    name = "auth" if name == "authentication" else name
                    api_list[name] = request.build_absolute_uri(os.path.join(name, ''))

        return response.Response(api_list)


urlpatterns = [
    path('', EndpointListView.as_view(), name='endpoint list'),
    path('admin/', admin.site.urls),
    path('auth/', include('authentication.urls'), name='authentication urls'),
    path('users/', include('users.urls'), name='users urls'),
]
