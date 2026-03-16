import logging

from config.celery import celery
from datetime import datetime, timedelta
from django.db.models import Q, Sum
from django.db.models.functions import Coalesce
from django.utils.timezone import now

from fee.models import FeeRate, UserFeeLevel
from lib.datetime import TZ_ASIA_SEOUL
from lib.search import search_closest_number
from users.models import DepositHistory, User

logger = logging.getLogger(__name__)


def _compute_fee_levels(user_fees, total_paid_fee_required_list):
    """Shared logic for computing fee levels from aggregated user fee totals."""
    results = {level: 0 for level in range(1, 7)}

    if not total_paid_fee_required_list:
        return results

    # Pre-fetch existing UserFeeLevel records
    existing_levels = {
        ufl.user_id: ufl
        for ufl in UserFeeLevel.objects.all()
    }

    bulk_create = []
    bulk_update = []

    for entry in user_fees:
        user_id = entry["id"]
        total_paid_fee = abs(entry["total_fee"] or 0)

        total_paid_fee_required = search_closest_number(
            total_paid_fee_required_list, total_paid_fee
        )
        try:
            fee_rate = FeeRate.objects.get(total_paid_fee_required=total_paid_fee_required)
        except FeeRate.DoesNotExist:
            continue

        user_fee_level = existing_levels.get(user_id)

        if user_fee_level:
            if user_fee_level.fee_level == -1 or user_fee_level.fee_level >= fee_rate.level:
                continue
            user_fee_level.fee_level = fee_rate.level
            user_fee_level.total_paid_fee = total_paid_fee
            user_fee_level.last_updated_datetime = now()
            bulk_update.append(user_fee_level)
        else:
            bulk_create.append(
                UserFeeLevel(
                    user_id=user_id,
                    fee_level=fee_rate.level,
                    total_paid_fee=total_paid_fee,
                )
            )

        results[fee_rate.level] = results.get(fee_rate.level, 0) + 1

    if bulk_create:
        UserFeeLevel.objects.bulk_create(bulk_create, ignore_conflicts=True)
    if bulk_update:
        UserFeeLevel.objects.bulk_update(
            bulk_update, ["fee_level", "total_paid_fee", "last_updated_datetime"]
        )

    return results


@celery.task
def compute_user_monthly_fee_level():
    """This task is scheduled to run every 1st day of the month, to compute fee levels for last month"""

    today = datetime.now(tz=TZ_ASIA_SEOUL)
    last_month = today - timedelta(days=1)
    last_month_first_day = last_month.replace(
        day=1,
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )
    last_month_last_day = last_month.replace(
        hour=23,
        minute=59,
        second=59,
        microsecond=timedelta.max.microseconds,
    )

    total_paid_fee_required_list = list(
        FeeRate.objects.values_list("total_paid_fee_required", flat=True)
    )

    # Single query: annotate from User side to include ALL users (even with 0 fees)
    user_fees = (
        User.objects.annotate(
            total_fee=Coalesce(
                Sum(
                    "deposithistory__change",
                    filter=Q(
                        deposithistory__type=DepositHistory.FEE,
                        deposithistory__registered_datetime__gte=last_month_first_day,
                        deposithistory__registered_datetime__lte=last_month_last_day,
                    ),
                ),
                0,
            )
        )
        .values("id", "total_fee")
    )

    return _compute_fee_levels(user_fees, total_paid_fee_required_list)


@celery.task
def compute_user_fee_level():
    """
    This task calculates the total accumulated fee spent by each user and updates their fee level accordingly.
    """

    total_paid_fee_required_list = list(
        FeeRate.objects.values_list("total_paid_fee_required", flat=True)
    )

    # Single query: annotate from User side to include ALL users (even with 0 fees)
    user_fees = (
        User.objects.annotate(
            total_fee=Coalesce(
                Sum(
                    "deposithistory__change",
                    filter=Q(deposithistory__type=DepositHistory.FEE),
                ),
                0,
            )
        )
        .values("id", "total_fee")
    )

    return _compute_fee_levels(user_fees, total_paid_fee_required_list)
