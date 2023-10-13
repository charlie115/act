import random

from datetime import datetime
from lib.random.providers.adjectives import adjectives
from lib.random.providers.nouns import nouns


def get_client_ip(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip


def generate_username():
    random_adjective = random.choice(adjectives)
    random_noun = random.choice(nouns)
    random_number = str(datetime.now().microsecond)[:3]
    return f"{random_adjective}{random_noun}{random_number}"
