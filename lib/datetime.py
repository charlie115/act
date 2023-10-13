from datetime import timedelta
from dateutil.parser import parse as parse_datestr


KST = "KST"
ASIA_SEOUL_TZ = "Asia/Seoul"

DATE_FORMAT_NUM = "%Y%m%d"
DATE_FORMAT = "%Y-%m-%d"
DATE_TIME_FORMAT = "%Y-%m-%dT%H:%M:%S"
ONE_DAY_IN_SECONDS = 86400


def create_list_of_dates(start_time, end_time, strformat=DATE_FORMAT):
    """Gives list of dates between start_time and end_time

    :param start_time: start date to create list of dates from
    :param end_time: end date to create list of dates from
    :return: list of dates
    """

    start_date = parse_datestr(start_time).replace(hour=0)
    end_date = parse_datestr(end_time).replace(hour=23)

    period_length = (end_date - start_date).days

    date_list = [start_date + timedelta(days=day) for day in range(period_length + 1)]
    date_list = [date.date().strftime(strformat) for date in date_list]

    return date_list
