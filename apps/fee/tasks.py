from config.celery import celery
from datetime import datetime, timedelta
from django.utils.timezone import now

from fee.models import FeeRate, UserFeeLevel
from lib.datetime import TZ_ASIA_SEOUL
from lib.search import search_closest_number
from users.models import DepositHistory, User


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
            print(err)

        results[fee_rate.level] += 1

    return results
