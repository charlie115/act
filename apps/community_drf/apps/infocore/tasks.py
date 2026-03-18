import logging
import time

from config.celery import celery
from domains.marketdata import (
    check_volatility_notifications_service,
    cleanup_old_notification_history_service,
)

logger = logging.getLogger(__name__)

MAX_FETCH_FAILURES = 5  # Stop retrying after this many consecutive failures
RATE_LIMIT_DELAY = 2.5  # 2.5s between requests = ~24 req/min (CoinMarketCap free: 30/min)
MAX_ICONS_PER_RUN = 10  # Process max 10 assets per task run to stay within rate limits


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
    from django.utils import timezone
    from infocore.models import Asset
    from infocore.mixins import AssetMixin

    mixin = AssetMixin()
    missing_list = []

    for asset in Asset.objects.all():
        # Skip assets that have exceeded max fetch failures
        if asset.icon_fetch_failures >= MAX_FETCH_FAILURES:
            continue

        if not asset.icon:
            missing_list.append(asset)
        else:
            try:
                if not default_storage.exists(asset.icon.name):
                    missing_list.append(asset)
            except Exception:
                missing_list.append(asset)

    total = len(missing_list)
    batch = missing_list[:MAX_ICONS_PER_RUN]  # Process only a batch per run
    filled = 0
    failed = 0

    for asset in batch:
        try:
            time.sleep(RATE_LIMIT_DELAY)  # Rate limit: max 5 req/s
            info = mixin.pull_asset_info(asset.symbol)

            time.sleep(RATE_LIMIT_DELAY)  # Rate limit for logo fetch
            icon = mixin.get_icon_image(info)

            if icon:
                asset.icon = icon
                asset.icon_fetch_failures = 0
                asset.icon_fetch_last_error = ""
                asset.icon_fetch_last_attempt_at = timezone.now()
                asset.save(update_fields=["icon", "icon_fetch_failures", "icon_fetch_last_error", "icon_fetch_last_attempt_at"])
                filled += 1
            else:
                asset.icon_fetch_failures += 1
                asset.icon_fetch_last_error = "get_icon_image returned None"
                asset.icon_fetch_last_attempt_at = timezone.now()
                asset.save(update_fields=["icon_fetch_failures", "icon_fetch_last_error", "icon_fetch_last_attempt_at"])
                failed += 1

        except Exception as e:
            asset.icon_fetch_failures += 1
            asset.icon_fetch_last_error = str(e)[:500]
            asset.icon_fetch_last_attempt_at = timezone.now()
            asset.save(update_fields=["icon_fetch_failures", "icon_fetch_last_error", "icon_fetch_last_attempt_at"])
            failed += 1
            logger.warning("backfill_missing_asset_icons|Failed for %s (attempt %d): %s", asset.symbol, asset.icon_fetch_failures, e)

    logger.info("backfill_missing_asset_icons|Filled %d/%d (batch %d), failed %d, skipped(max_failures) %d",
                filled, total, len(batch), failed, Asset.objects.filter(icon_fetch_failures__gte=MAX_FETCH_FAILURES).count())
