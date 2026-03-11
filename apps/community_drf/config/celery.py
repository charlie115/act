import os
import sys
import logging

from celery import Celery
from celery.schedules import crontab
from django.conf import settings
from environ import Env
from pathlib import Path


BASE_DIR = Path(__file__).resolve(strict=True).parent.parent
sys.path.append(str(BASE_DIR / "apps"))

env = Env(DEBUG=(bool, False))
Env.read_env(os.path.join(BASE_DIR, ".env"))

DJANGO_SETTINGS_MODULE = env("DJANGO_SETTINGS_MODULE")

celery = Celery("config")
celery.config_from_object("django.conf:settings", namespace="CELERY")
celery.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

celery.conf.beat_schedule = {
    # Disable the monthly fee-level computation task
    # "compute-user-monthly-fee-level": {
    #     "task": "fee.tasks.compute_user_monthly_fee_level",
    #     "schedule": crontab(hour=0, minute=5, day_of_month=1),
    # },
    "compute_user_fee_level": {
        "task": "fee.tasks.compute_user_fee_level",
        "schedule": crontab(minute="*"),  # Runs every minute
    },
    "check_volatility_notifications": {
        "task": "infocore.tasks.check_volatility_notifications",
        "schedule": 30.0,  # Runs every 30 seconds
    },
    "cleanup_old_notification_history": {
        "task": "infocore.tasks.cleanup_old_notification_history",
        "schedule": crontab(hour=3, minute=0),  # Runs daily at 3 AM
    },
}

logger = logging.getLogger(__name__)

@celery.task(bind=True, ignore_result=True)
def debug_task(self):
    logger.info("Celery debug task request: %r", self.request)
