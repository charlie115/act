from time import sleep
import pandas as pd
import datetime

# global variable
# DOLLAR_INFO_DICT

# def fetch_dollar(return_dict, update_dollar_logger, url='https://search.naver.com/search.naver?where=nexearch&sm=top_hty&fbm=1&ie=utf8&query=%ED%99%98%EC%9C%A8%EC%A1%B0%ED%9A%8C', timedelta_hours=9):
def fetch_dollar(return_dict, update_dollar_logger, url='https://finance.naver.com/marketindex/exchangeDegreeCountQuote.naver?marketindexCd=FX_USDKRW', timedelta_hours=9):
    # global DOLLAR_INFO_DICT
    # return_dict = {
    #     'price': None,
    #     'change': None,
    #     'last_updated_time': None
    # }
    try:
        exchange_rate = pd.read_html(url)[0]
        return_dict['price'] = exchange_rate.iloc[0,1]
        # return_dict['change'] = exchange_rate.iloc[0,-1]
        return_dict['change'] = exchange_rate.iloc[0,2]
        return_dict['last_updated_time'] = datetime.datetime.now()
        update_dollar_logger.info(f"fetch_dollar|Dollar price ({return_dict['price']} KRW) has been updated.")
    except Exception as e:
        # print(f'Except executed in get_dollar function, {e}')
        update_dollar_logger.warning(f"fetch_dollar|Exception occured! Error: {e}, pd.read_html(url): {pd.read_html(url)}")
        exchange_rate = pd.read_html(url)[1]
        return_dict['price'] = exchange_rate.iloc[0,1]
        # return_dict['change'] = exchange_rate.iloc[0,-1]
        return_dict['change'] = exchange_rate.iloc[0,2]
        return_dict['last_updated_time'] = datetime.datetime.now()
    return return_dict

def fetch_dollar_loop(return_dict, update_dollar_logger, loop_time=30):
    while True:
        fetch_dollar(return_dict, update_dollar_logger)
        sleep(loop_time)