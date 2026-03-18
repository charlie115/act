import logging

from config.celery import celery
from domains.marketdata import (
    check_volatility_notifications_service,
    cleanup_old_notification_history_service,
)

logger = logging.getLogger(__name__)


@celery.task(bind=True, autoretry_for=(Exception,), retry_backoff=30, max_retries=3, retry_jitter=True)
def check_volatility_notifications(self):
    return check_volatility_notifications_service()


@celery.task(bind=True, autoretry_for=(Exception,), retry_backoff=30, max_retries=3, retry_jitter=True)
def cleanup_old_notification_history(self, days_to_keep=7):
    return cleanup_old_notification_history_service(days_to_keep=days_to_keep)


@celery.task(bind=True, autoretry_for=(Exception,), retry_backoff=30, max_retries=3, retry_jitter=True)
def backfill_missing_asset_icons(self):
    """Fetch icons from CoinMarketCap for assets that have no icon or whose icon file is missing from storage."""
    from django.core.files.storage import default_storage
    from infocore.models import Asset
    from infocore.mixins import AssetMixin

    mixin = AssetMixin()
    missing_list = []

    for asset in Asset.objects.all():
        if not asset.icon:
            missing_list.append(asset)
        else:
            try:
                if not default_storage.exists(asset.icon.name):
                    missing_list.append(asset)
            except Exception:
                missing_list.append(asset)

    total = len(missing_list)
    filled = 0

    for asset in missing_list:
        try:
            info = mixin.pull_asset_info(asset.symbol)
            icon = mixin.get_icon_image(info)
            if icon:
                asset.icon = icon
                asset.save(update_fields=["icon"])
                filled += 1
        except Exception:
            logger.warning("backfill_missing_asset_icons|Failed for %s", asset.symbol, exc_info=True)

    logger.info("backfill_missing_asset_icons|Filled %d/%d missing icons", filled, total)
