import logging
from datetime import timedelta

from django.utils import timezone

from infocore.models import VolatilityNotificationConfig, VolatilityNotificationHistory
from messagecore.models import Message
from platform_common.integrations.infocore import get_infocore_mongo_client


logger = logging.getLogger(__name__)
MONGODB_CLI = get_infocore_mongo_client(appname="django-marketdata-volatility")


def fetch_volatility_data(target_market_code, origin_market_code, base_assets=None):
    try:
        database = (
            target_market_code.replace("/", "__")
            + "-"
            + origin_market_code.replace("/", "__")
        )
        collection = "volatility_info"

        db = MONGODB_CLI.get_database(database)
        coll = db.get_collection(collection)

        pipeline = []
        if base_assets:
            pipeline.append({"$match": {"base_asset": {"$in": base_assets}}})

        pipeline.append({"$sort": {"datetime_now": -1}})
        pipeline.append({"$group": {"_id": "$base_asset", "data": {"$first": "$$ROOT"}}})

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
    except Exception:
        logger.exception(
            "fetch_volatility_data failed for %s:%s",
            target_market_code,
            origin_market_code,
        )
        return []


def create_notification_message(user, config, alerts):
    if not user.telegram_chat_id:
        logger.warning("User %s has no telegram_chat_id configured", user.email)
        return False

    user_socialapp = user.socialapps.filter(socialapp__provider="telegram").first()
    if not user_socialapp:
        logger.warning("User %s has no linked Telegram bot", user.email)
        return False

    telegram_bot_username = user_socialapp.socialapp.client_id
    market_pair = f"{config.target_market_code}:{config.origin_market_code}"
    threshold = float(config.volatility_threshold)

    alert_lines = []
    for alert in sorted(alerts, key=lambda x: x["mean_diff"], reverse=True)[:15]:
        alert_lines.append(f"  {alert['base_asset']}: {alert['mean_diff']:.4f}")

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
    except Exception:
        logger.exception(
            "create_notification_message failed for user=%s config=%s",
            user.email,
            config.id,
        )
        return False


def check_volatility_notifications_service():
    now = timezone.now()
    stats = {
        "configs_checked": 0,
        "notifications_sent": 0,
        "symbols_notified": 0,
        "configs_skipped_no_alerts": 0,
        "errors": 0,
    }

    configs = VolatilityNotificationConfig.objects.filter(enabled=True).select_related("user")

    for config in configs:
        stats["configs_checked"] += 1
        try:
            volatility_data = fetch_volatility_data(
                config.target_market_code,
                config.origin_market_code,
                config.base_assets,
            )

            threshold = float(config.volatility_threshold)
            exceeding_assets = [
                item
                for item in volatility_data
                if item.get("mean_diff", 0) >= threshold
            ]
            if not exceeding_assets:
                stats["configs_skipped_no_alerts"] += 1
                continue

            interval_cutoff = now - timedelta(minutes=config.notification_interval_minutes)
            recently_notified = set(
                VolatilityNotificationHistory.objects.filter(
                    config=config,
                    notified_at__gte=interval_cutoff,
                ).values_list("base_asset", flat=True)
            )
            new_alerts = [
                item for item in exceeding_assets if item["base_asset"] not in recently_notified
            ]

            if not new_alerts:
                stats["configs_skipped_no_alerts"] += 1
                continue

            if create_notification_message(config.user, config, new_alerts):
                VolatilityNotificationHistory.objects.bulk_create(
                    [
                        VolatilityNotificationHistory(
                            config=config,
                            base_asset=alert["base_asset"],
                            mean_diff=alert["mean_diff"],
                        )
                        for alert in new_alerts
                    ]
                )
                stats["notifications_sent"] += 1
                stats["symbols_notified"] += len(new_alerts)
        except Exception:
            logger.exception("check_volatility_notifications failed for config=%s", config.id)
            stats["errors"] += 1

    return stats


def cleanup_old_notification_history_service(days_to_keep=7):
    cutoff_date = timezone.now() - timedelta(days=days_to_keep)
    deleted_count, _ = VolatilityNotificationHistory.objects.filter(
        notified_at__lt=cutoff_date
    ).delete()
    return {"deleted_records": deleted_count}
