from config.celery import celery
from domains.marketdata import (
    check_volatility_notifications_service,
    cleanup_old_notification_history_service,
)


@celery.task
def check_volatility_notifications():
    return check_volatility_notifications_service()


@celery.task
def cleanup_old_notification_history(days_to_keep=7):
    return cleanup_old_notification_history_service(days_to_keep=days_to_keep)
