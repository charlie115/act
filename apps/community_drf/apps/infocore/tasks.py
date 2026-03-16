import logging

from config.celery import celery
from domains.marketdata import (
    check_volatility_notifications_service,
    cleanup_old_notification_history_service,
)

logger = logging.getLogger(__name__)


@celery.task
def check_volatility_notifications():
    return check_volatility_notifications_service()


@celery.task
def cleanup_old_notification_history(days_to_keep=7):
    return cleanup_old_notification_history_service(days_to_keep=days_to_keep)


@celery.task
def backfill_missing_asset_icons():
    """Fetch icons from CoinMarketCap for assets that have no icon."""
    from infocore.models import Asset
    from infocore.mixins import AssetMixin

    mixin = AssetMixin()
    missing = Asset.objects.filter(icon="")
    filled = 0

    for asset in missing:
        try:
            info = mixin.pull_asset_info(asset.symbol)
            icon = mixin.get_icon_image(info)
            if icon:
                asset.icon = icon
                asset.save(update_fields=["icon"])
                filled += 1
        except Exception:
            logger.warning("backfill_missing_asset_icons|Failed for %s", asset.symbol)

    logger.info("backfill_missing_asset_icons|Filled %d/%d missing icons", filled, missing.count())
