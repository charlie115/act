from datetime import timedelta
from pytz import timezone, utc


UTC = "UTC"
KST = "KST"
ASIA_SEOUL = "Asia/Seoul"
TZ_UTC = utc
TZ_ASIA_SEOUL = timezone(ASIA_SEOUL)

DATE_FORMAT_NUM = "%Y%m%d"
DATE_FORMAT = "%Y-%m-%d"
DATE_TIME_FORMAT = "%Y-%m-%dT%H:%M:%S"
DATE_TIME_TZ_FORMAT = "%Y-%m-%dT%H:%M:%S%z"
ONE_DAY_IN_SECONDS = 86400


def create_list_of_dates(start_time, end_time, strformat=DATE_FORMAT):
    """Gives list of dates between start_time and end_time

    :param start_time: start date to create list of dates from
    :param end_time: end date to create list of dates from
    :return: list of dates
    """

    start_date = start_time.replace(hour=0)
    end_date = end_time.replace(hour=23)

    period_length = (end_date - start_date).days

    date_list = [start_date + timedelta(days=day) for day in range(period_length + 1)]
    date_list = [date.date().strftime(strformat) for date in date_list]

    return date_list
