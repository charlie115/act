import logging

from config.celery import celery
from datetime import datetime, timedelta
from django.utils.timezone import now

from fee.models import FeeRate, UserFeeLevel
from lib.datetime import TZ_ASIA_SEOUL
from lib.search import search_closest_number
from users.models import DepositHistory, User

logger = logging.getLogger(__name__)

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

    results = {
        1: 0,
        2: 0,
        3: 0,
        4: 0,
        5: 0,
    }
    for user in User.objects.all():
        deposit_history = DepositHistory.objects.filter(
            user=user,
            type=DepositHistory.FEE,
            registered_datetime__gte=last_month_first_day,
            registered_datetime__lte=last_month_last_day,
        )

        total_paid_fee = abs(sum(deposit_history.values_list("change", flat=True)))
        total_paid_fee_required = search_closest_number(
            total_paid_fee_required_list, total_paid_fee
        )

        fee_rate = FeeRate.objects.get(total_paid_fee_required=total_paid_fee_required)

        try:
            user_fee_level = UserFeeLevel.objects.get(user=user)
            # Prevent updating fee level if the user's fee_level is -1(specified by admin) or higher than the calculated fee level
            if user_fee_level.fee_level == -1 or user_fee_level.fee_level >= fee_rate.level:
                continue
            user_fee_level.fee_level = fee_rate.level
            user_fee_level.total_paid_fee = total_paid_fee
            user_fee_level.last_updated_datetime = now()
            user_fee_level.save()
        except UserFeeLevel.DoesNotExist:
            user_fee_level = UserFeeLevel.objects.create(
                user=user,
                fee_level=fee_rate.level,
                total_paid_fee=total_paid_fee,
            )
        except Exception as err:
            logger.exception("Error updating monthly fee level for user=%s", user.id)

        results[fee_rate.level] += 1

    return results

@celery.task
def compute_user_fee_level():
    """
    This task calculates the total accumulated fee spent by each user and updates their fee level accordingly.
    It no longer focuses on last month's fees, but on all fees accumulated over time.
    """

    # Fetch all the total_paid_fee_required values to determine fee levels
    total_paid_fee_required_list = list(
        FeeRate.objects.values_list("total_paid_fee_required", flat=True)
    )

    results = {
        1: 0,
        2: 0,
        3: 0,
        4: 0,
        5: 0,
        6: 0,
    }

    for user in User.objects.all():
        # Fetch all fee deposit history records for the user
        deposit_history = DepositHistory.objects.filter(
            user=user,
            type=DepositHistory.FEE,
        )

        # Sum the 'change' values and take the absolute (assuming 'change' might be negative)
        total_paid_fee = abs(sum(deposit_history.values_list("change", flat=True)))

        # Determine which fee_level is closest to the user's total_paid_fee
        if not total_paid_fee_required_list:
            # If no fee rates are defined, skip processing
            continue

        total_paid_fee_required = search_closest_number(
            total_paid_fee_required_list, total_paid_fee
        )

        fee_rate = FeeRate.objects.get(total_paid_fee_required=total_paid_fee_required)

        try:
            user_fee_level = UserFeeLevel.objects.get(user=user)
            # If user's fee_level is -1 (locked by admin) or already higher or equal, don't downgrade
            if user_fee_level.fee_level == -1 or user_fee_level.fee_level >= fee_rate.level:
                continue

            user_fee_level.fee_level = fee_rate.level
            user_fee_level.total_paid_fee = total_paid_fee
            user_fee_level.last_updated_datetime = now()
            user_fee_level.save()

        except UserFeeLevel.DoesNotExist:
            # If there's no existing record, create a new one
            UserFeeLevel.objects.create(
                user=user,
                fee_level=fee_rate.level,
                total_paid_fee=total_paid_fee,
            )
        except Exception as err:
            logger.exception("Error updating fee level for user=%s", user.id)

        # Increment results counter for this fee level
        results[fee_rate.level] += 1

    return results
