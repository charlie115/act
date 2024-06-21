from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _


UNFOLD = {
    "SITE_TITLE": "Django Admin",
    "SITE_HEADER": "Django Admin",
    "SITE_URL": "/",
    "SITE_SYMBOL": "settings",  # symbol from icon set
    "SHOW_HISTORY": False,  # show/hide "History" button, default: True
    "SHOW_VIEW_ON_SITE": True,  # show/hide "View on site" button, default: True
    "ENVIRONMENT": "lib.utils.unfold_environment_callback",
    "SIDEBAR": {
        "show_search": True,  # Search in applications and models names
        "show_all_applications": True,  # Dropdown with all applications and models
        "navigation": [
            {
                "title": _("ACW"),
                "separator": True,  # Top border
                "items": [
                    # {
                    #     "title": _("Dashboard"),
                    #     "icon": "dashboard",  # Supported icon set: https://fonts.google.com/icons
                    #     "link": reverse_lazy("admin:index"),
                    #     "badge": "sample_app.badge_callback",
                    #     "permission": lambda request: request.user.is_superuser,
                    # },
                    {
                        "title": _("Users"),
                        "icon": "people",
                        "link": reverse_lazy("admin:users_user_changelist"),
                    },
                    {
                        "title": _("Deposit Balance"),
                        "icon": "account_balance_wallet",
                        "link": reverse_lazy("admin:users_depositbalance_changelist"),
                    },
                    {
                        "title": _("Fee Levels"),
                        "icon": "money",
                        "link": reverse_lazy("admin:fee_userfeelevel_changelist"),
                    },
                    {
                        "title": _("Referral System"),
                        "icon": "confirmation_number",
                        "link": reverse_lazy("admin:referral_referral_changelist"),
                    },
                    {
                        "title": _("Social Apps"),
                        "icon": "deployed_code_account",
                        "link": reverse_lazy(
                            "admin:socialaccounts_proxysocialapp_changelist"
                        ),
                    },
                    {
                        "title": _("Board"),
                        "icon": "forum",
                        "link": reverse_lazy("admin:board_post_changelist"),
                    },
                ],
            },
            {
                "title": _("CORE"),
                "separator": True,
                "items": [
                    {
                        "title": _("INFO"),
                        "icon": "sync_alt",
                        "link": reverse_lazy("admin:infocore_marketcode_changelist"),
                    },
                    {
                        "title": _("TRADE"),
                        "icon": "candlestick_chart",
                        "link": reverse_lazy(
                            "admin:tradecore_enabledmarketcodecombination_changelist"
                        ),
                    },
                    {
                        "title": _("MESSAGE"),
                        "icon": "outgoing_mail",
                        "link": reverse_lazy("admin:messagecore_message_changelist"),
                    },
                ],
            },
            {
                "title": _(""),
                "separator": True,
                "items": [
                    {
                        "title": _("Groups"),
                        "icon": "groups_2",
                        "link": reverse_lazy(
                            "admin:authentication_proxygroup_changelist"
                        ),
                    },
                    {
                        "title": _("Roles & API Permissions"),
                        "icon": "admin_panel_settings",
                        "link": reverse_lazy("admin:users_userrole_changelist"),
                    },
                    {
                        "title": _("Tasks"),
                        "icon": "task_alt",
                        "link": reverse_lazy(
                            "admin:django_celery_beat_periodictask_changelist"
                        ),
                    },
                ],
            },
        ],
    },
    "TABS": [
        {
            "models": [
                "users.user",
                "users.usermanagement",
                "users.userblocklist",
            ],
            "items": [
                {
                    "title": _("Users"),
                    "icon": "people",
                    "link": reverse_lazy("admin:users_user_changelist"),
                },
                {
                    "title": _("User Management"),
                    "link": reverse_lazy("admin:users_usermanagement_changelist"),
                },
                {
                    "title": _("User Blocklist"),
                    "link": reverse_lazy("admin:users_userblocklist_changelist"),
                },
            ],
        },
        {
            "models": [
                "users.depositbalance",
                "users.deposithistory",
            ],
            "items": [
                {
                    "title": _("Deposit Balance"),
                    "icon": "account_balance_wallet",
                    "link": reverse_lazy("admin:users_depositbalance_changelist"),
                },
                {
                    "title": _("Deposit History"),
                    "link": reverse_lazy("admin:users_deposithistory_changelist"),
                },
            ],
        },
        {
            "models": [
                "fee.userfeelevel",
                "fee.feerate",
            ],
            "items": [
                {
                    "title": _("User Fee Levels"),
                    "icon": "money",
                    "link": reverse_lazy("admin:fee_userfeelevel_changelist"),
                },
                {
                    "title": _("Fee Rate"),
                    "link": reverse_lazy("admin:fee_feerate_changelist"),
                },
            ],
        },
        {
            "models": [
                "referral.referralgroup",
                "referral.referralcode",
                "referral.referral",
            ],
            "items": [
                {
                    "title": _("Referrals"),
                    "icon": "partner_exchange",
                    "link": reverse_lazy("admin:referral_referral_changelist"),
                },
                {
                    "title": _("Referral Code"),
                    "icon": "confirmation_number",
                    "link": reverse_lazy("admin:referral_referralcode_changelist"),
                },
                {
                    "title": _("Referral Group"),
                    "icon": "diversity_3",
                    "link": reverse_lazy("admin:referral_referralgroup_changelist"),
                },
            ],
        },
        {
            "models": [
                "tradecore.node",
                "tradecore.tradeconfigallocation",
                "tradecore.enabledmarketcodecombination",
            ],
            "items": [
                {
                    "title": _("Enabled Market Code Combinations"),
                    "icon": "sync_alt",
                    "link": reverse_lazy(
                        "admin:tradecore_enabledmarketcodecombination_changelist"
                    ),
                },
                {
                    "title": _("Nodes"),
                    "icon": "dns",
                    "link": reverse_lazy("admin:tradecore_node_changelist"),
                },
                {
                    "title": _("Trade Config Allocations"),
                    "icon": "add_chart",
                    "link": reverse_lazy(
                        "admin:tradecore_tradeconfigallocation_changelist"
                    ),
                },
            ],
        },
        {
            "models": [
                "infocore.marketcode",
                "infocore.asset",
            ],
            "items": [
                {
                    "title": _("Market Code"),
                    "icon": "sync_alt",
                    "link": reverse_lazy("admin:infocore_marketcode_changelist"),
                },
                {
                    "title": _("Assets"),
                    "link": reverse_lazy("admin:infocore_asset_changelist"),
                },
            ],
        },
        {
            "models": [
                "users.userrole",
                "api.permission",
            ],
            "items": [
                {
                    "title": _("Roles"),
                    "link": reverse_lazy("admin:users_userrole_changelist"),
                },
                {
                    "title": _("API Permissions"),
                    "link": reverse_lazy("admin:api_permission_changelist"),
                },
            ],
        },
        {
            "models": [
                "socialaccounts.proxysocialapp",
                "socialaccounts.proxysocialaccount",
            ],
            "items": [
                {
                    "title": _("Social Apps"),
                    "link": reverse_lazy(
                        "admin:socialaccounts_proxysocialapp_changelist"
                    ),
                },
                {
                    "title": _("Social Accounts"),
                    "link": reverse_lazy(
                        "admin:socialaccounts_proxysocialaccount_changelist"
                    ),
                },
            ],
        },
        {
            "models": [
                "board.postcategory",
                "board.post",
                "board.comment",
            ],
            "items": [
                {
                    "title": _("Posts"),
                    "link": reverse_lazy("admin:board_post_changelist"),
                },
                {
                    "title": _("Comments"),
                    "link": reverse_lazy("admin:board_comment_changelist"),
                },
                {
                    "title": _("Categories"),
                    "link": reverse_lazy("admin:board_postcategory_changelist"),
                },
            ],
        },
        {
            "models": [
                "django_celery_beat.periodictask",
                "django_celery_results.taskresult",
            ],
            "items": [
                {
                    "title": _("Tasks"),
                    "icon": "task_alt",
                    "link": reverse_lazy(
                        "admin:django_celery_beat_periodictask_changelist"
                    ),
                },
                {
                    "title": _("Task Results"),
                    "link": reverse_lazy(
                        "admin:django_celery_results_taskresult_changelist"
                    ),
                },
            ],
        },
    ],
    "EXTENSIONS": {
        "modeltranslation": {
            "flags": {
                "en": "🇬🇧",
                "kr": "🇰🇷",
                "ch": "🇨🇳",
            },
        },
    },
}
