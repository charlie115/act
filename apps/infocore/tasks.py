"""
Celery tasks for infocore app.

This module contains periodic tasks for monitoring volatility thresholds
and creating notifications when thresholds are exceeded.
"""

from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from pymongo import MongoClient

from config.celery import celery
from infocore.models import VolatilityNotificationConfig
from messagecore.models import Message


# MongoDB client for fetching volatility data
MONGODB_CLI = MongoClient(
    host=settings.MONGODB["HOST"],
    port=settings.MONGODB["PORT"],
    username=settings.MONGODB["USERNAME"],
    password=settings.MONGODB["PASSWORD"],
    appname="django-infocore-tasks",
)


def fetch_volatility_data(target_market_code, origin_market_code, base_assets=None):
    """
    Fetch volatility data from MongoDB.

    Args:
        target_market_code: e.g., "UPBIT_SPOT/KRW"
        origin_market_code: e.g., "BINANCE_USD_M/USDT"
        base_assets: Optional list of base assets to filter, e.g., ["BTC", "ETH"]

    Returns:
        List of dicts with 'base_asset' and 'mean_diff' keys
    """
    try:
        # Construct database name (same pattern as KlineVolatilityView)
        database = (
            target_market_code.replace("/", "__")
            + "-"
            + origin_market_code.replace("/", "__")
        )
        collection = "volatility_info"

        db = MONGODB_CLI.get_database(database)
        coll = db.get_collection(collection)

        # Build aggregation pipeline
        pipeline = []
        if base_assets:
            pipeline.append({"$match": {"base_asset": {"$in": base_assets}}})

        # Group by base_asset and get the latest document
        pipeline.append(
            {"$sort": {"datetime_now": -1}}
        )
        pipeline.append(
            {"$group": {"_id": "$base_asset", "data": {"$first": "$$ROOT"}}}
        )

        cursor = coll.aggregate(pipeline)

        results = []
        for item in cursor:
            data = item.get("data", {})
            results.append(
                {
                    "base_asset": data.get("base_asset", item["_id"]),
                    "mean_diff": data.get("mean_diff", 0),
                }
            )

        return results

    except Exception as e:
        print(f"Error fetching volatility data: {e}")
        return []


def create_notification_message(user, config, alerts):
    """
    Create a Message record for Telegram delivery.

    Args:
        user: User instance
        config: VolatilityNotificationConfig instance
        alerts: List of dicts with 'base_asset' and 'mean_diff' keys

    Returns:
        True if message was created, False otherwise
    """
    # Validate user has telegram setup
    if not user.telegram_chat_id:
        print(f"User {user.email} has no telegram_chat_id configured")
        return False

    # Get user's linked telegram bot
    user_socialapp = user.socialapps.filter(socialapp__provider="telegram").first()
    if not user_socialapp:
        print(f"User {user.email} has no linked Telegram bot")
        return False

    telegram_bot_username = user_socialapp.socialapp.client_id

    # Build message content
    market_pair = f"{config.target_market_code}:{config.origin_market_code}"

    # Format threshold as raw number
    threshold = float(config.volatility_threshold)

    # Format alerts (limit to 15 to avoid overly long messages)
    alert_lines = []
    for alert in sorted(alerts, key=lambda x: x["mean_diff"], reverse=True)[:15]:
        mean_diff = alert["mean_diff"]
        alert_lines.append(f"  {alert['base_asset']}: {mean_diff:.4f}")

    content = (
        f"마켓: {market_pair}\n"
        f"설정 임계값: {threshold:.4f}\n\n"
        f"임계값 초과 종목:\n" + "\n".join(alert_lines)
    )

    if len(alerts) > 15:
        content += f"\n\n... 외 {len(alerts) - 15}개 종목"

    try:
        Message.objects.create(
            telegram_chat_id=int(user.telegram_chat_id),
            telegram_bot_username=telegram_bot_username,
            title="변동성 알림",
            content=content,
            origin="volatility_monitor",
            type=Message.INFO,
            sent=False,
        )
        return True
    except Exception as e:
        print(f"Error creating notification message: {e}")
        return False


@celery.task
def check_volatility_notifications():
    """
    Periodic task that checks all enabled volatility notification configs
    and creates notifications when thresholds are exceeded.

    This task:
    1. Fetches all enabled VolatilityNotificationConfig entries
    2. For each config, checks if enough time has passed since last notification
    3. Fetches current volatility data from MongoDB
    4. If any asset exceeds the threshold, creates a Message for Telegram delivery
    5. Updates last_notified_at timestamp

    Returns:
        dict with statistics about the task run
    """
    now = timezone.now()
    stats = {
        "configs_checked": 0,
        "notifications_sent": 0,
        "configs_skipped_interval": 0,
        "configs_skipped_no_alerts": 0,
        "errors": 0,
    }

    # Fetch all enabled configs with related user data
    configs = VolatilityNotificationConfig.objects.filter(
        enabled=True
    ).select_related("user")

    for config in configs:
        stats["configs_checked"] += 1

        try:
            # Check rate limiting: skip if within notification interval
            if config.last_notified_at:
                elapsed_minutes = (now - config.last_notified_at).total_seconds() / 60
                if elapsed_minutes < config.notification_interval_minutes:
                    stats["configs_skipped_interval"] += 1
                    continue

            # Fetch volatility data from MongoDB
            volatility_data = fetch_volatility_data(
                config.target_market_code,
                config.origin_market_code,
                config.base_assets,
            )

            # Find assets exceeding threshold
            threshold = float(config.volatility_threshold)
            alerts = [
                item
                for item in volatility_data
                if item.get("mean_diff", 0) >= threshold
            ]

            if not alerts:
                stats["configs_skipped_no_alerts"] += 1
                continue

            # Create notification message
            success = create_notification_message(config.user, config, alerts)

            if success:
                # Update last_notified_at
                config.last_notified_at = now
                config.save(update_fields=["last_notified_at"])
                stats["notifications_sent"] += 1

        except Exception as e:
            print(f"Error processing config {config.id}: {e}")
            stats["errors"] += 1

    return stats
