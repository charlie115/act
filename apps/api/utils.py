from django.urls import get_resolver
from django.urls.resolvers import URLPattern, RegexPattern


def get_url_patterns(url_patterns, app_name=None):
    """
    Recursive function iterating urlpatterns to get all available API endpoints
    Please be careful when modifying the code since this is recursive.
    """

    result = []

    for url_pattern in url_patterns:
        if isinstance(url_pattern, URLPattern):
            app_name = app_name if app_name else None
            view = url_pattern.callback

            if (
                app_name
                and hasattr(view, "cls")
                and hasattr(url_pattern, "name")
                and "root" not in url_pattern.name
            ):
                app = app_name

                if type(url_pattern.pattern) is RegexPattern:
                    endpoint = (
                        url_pattern.pattern.regex.pattern.split("/")[0]
                        .split("\\")[0]
                        .split("(")[0]
                        .strip("^")
                        .strip("$")
                    )
                    if not endpoint and ":" in app_name:
                        app, endpoint = app_name.split(":")
                elif "view" in url_pattern.name:
                    app = app_name.split(":")[0]
                    endpoint = url_pattern.name.replace("-view", "")
                else:
                    endpoint = url_pattern.pattern._route.strip("/")

                methods = (
                    view.cls.http_method_names if hasattr(view, "cls") else "NO VIEW"
                )

                result.append((app, endpoint, methods))

        else:
            app_name = (
                url_pattern.app_name if hasattr(url_pattern, "app_name") else None
            )
            result.extend(get_url_patterns(url_pattern.url_patterns, app_name=app_name))

    return result


def get_api_permission_choices():
    results = get_url_patterns(get_resolver().url_patterns)

    all_api = dict()
    for result in results:
        app_name, endpoint, methods = result

        if app_name in all_api:
            if endpoint in all_api[app_name]:
                new_methods = list(set(all_api[app_name][endpoint]) - set(methods))
                if new_methods:
                    all_api[app_name][endpoint].extend(new_methods)
            else:
                all_api[app_name][endpoint] = methods
        else:
            all_api[app_name] = {endpoint: methods}

    permission_choices = []
    for app_name, data in all_api.items():
        if app_name not in ["authentication", "chat"]:
            endpoint_methods = [
                (
                    f"{app_name}_{method}_{endpoint}",
                    f"[{app_name}] {method.upper()} {endpoint}",
                )
                for endpoint, methods in data.items()
                for method in methods
            ]
            permission_choices.extend(endpoint_methods)

    return permission_choices
