import re
import random

from lib.random.providers.adjectives import adjectives
from lib.random.providers.nouns import nouns

NICKNAME_PATTERN = re.compile(r"^[a-zA-Z][a-zA-Z0-9_]{1,19}$")

RESERVED_NICKNAMES = [
    "admin",
    "system",
    "moderator",
    "bot",
    "staff",
    "support",
    "anonymous",
    "guest",
]

MAX_GENERATION_ATTEMPTS = 10


def validate_nickname_format(nickname):
    """Validate nickname matches the required format.

    Rules:
    - Must start with a letter
    - Only letters, digits, and underscores allowed
    - Length 2-20 characters

    Returns:
        (bool, str): (is_valid, error_message)
    """
    if not nickname:
        return False, "Nickname cannot be empty."
    if not NICKNAME_PATTERN.match(nickname):
        return False, (
            "Nickname must start with a letter, contain only letters, "
            "digits, and underscores, and be 2-20 characters long."
        )
    return True, ""


def validate_nickname_not_reserved(nickname):
    """Check that the nickname is not in the reserved blocklist.

    Returns:
        (bool, str): (is_valid, error_message)
    """
    if nickname.lower() in RESERVED_NICKNAMES:
        return False, "This nickname is reserved and cannot be used."
    return True, ""


def validate_nickname_unique(nickname, exclude_user_id=None):
    """Check that the nickname is unique (case-insensitive) against User.chat_nickname.

    Returns:
        (bool, str): (is_valid, error_message)
    """
    from users.models import User

    qs = User.objects.filter(chat_nickname__iexact=nickname)
    if exclude_user_id is not None:
        qs = qs.exclude(pk=exclude_user_id)
    if qs.exists():
        return False, "This nickname is already taken."
    return True, ""


def generate_chat_nickname():
    """Generate a unique PascalCase chat nickname from adjective + noun word lists.

    If the initial combination is a duplicate, append a 2-3 digit random number
    and retry (up to MAX_GENERATION_ATTEMPTS).

    Returns:
        str: A unique chat nickname.

    Raises:
        RuntimeError: If a unique nickname cannot be generated after max attempts.
    """
    from users.models import User

    for attempt in range(MAX_GENERATION_ATTEMPTS):
        adj = random.choice(adjectives).capitalize()
        noun = random.choice(nouns).capitalize()
        nickname = f"{adj}{noun}"

        if attempt > 0:
            suffix = str(random.randint(10, 999))
            nickname = f"{nickname}{suffix}"

        # Ensure it fits the 20-char limit
        if len(nickname) > 20:
            nickname = nickname[:20]

        # Check uniqueness (case-insensitive)
        if not User.objects.filter(chat_nickname__iexact=nickname).exists():
            return nickname

    raise RuntimeError(
        f"Failed to generate a unique chat nickname after {MAX_GENERATION_ATTEMPTS} attempts."
    )
