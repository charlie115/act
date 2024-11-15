import os
import sys
import traceback
from io import BytesIO
from io import TextIOWrapper, BytesIO
import datetime
import time
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as mtick
from sklearn import linear_model
from decimal import Decimal
from etc.db_handler.mongodb_client import InitDBClient
from loggers.logger import TradeCoreLogger
# library for candlestick
import mplfinance as mpf

# Skip any overhead related to the GUI backends.
import matplotlib
matplotlib.use('Agg')

def get_pboundary(mongo_db_dict, market_code_combination, base_asset, usdt_conversion, interval, kline_num, percent_gap, logging_dir, draw_plot=False, return_dict=None):
    mongo_db_client = InitDBClient(**mongo_db_dict)
    mongo_db_conn = mongo_db_client.get_conn()
    logger = TradeCoreLogger("data_process_logger", logging_dir).logger
    percent_gap = float(percent_gap)
    converted_market_code_combination = market_code_combination.replace('/', '__').replace(':', '-')
    try:
        if draw_plot:
            plt.clf()
            fig = plt.figure(figsize=(14,8))
            ax = plt.gca()
            ax.grid(True)
        
        # Load kimp_kline from DB
        # db_start = time.time()                                                      #test
        collection = mongo_db_conn[f"{converted_market_code_combination}"][f'{base_asset}_{interval}'].find({}).sort('_id', -1).limit(kline_num)
        fetched_df = pd.DataFrame(collection)
        # print(f"db fetch time: {time.time() - db_start}")                           #test
        premium_df = pd.DataFrame(fetched_df).drop('_id', axis=1).sort_values('datetime_now').reset_index(drop=True).drop_duplicates()
        # first check whether the collection exsits
        if len(premium_df) == 0:
            raise ValueError(f"Empty collection: {converted_market_code_combination}|{base_asset}|{interval} doesn't exist in DB")
        # check whether 'tp_close' column is full of NaN or null values
        if premium_df['tp_close'].isnull().all():
            premium_df.loc[:, 'tp_close'] = (premium_df['LS_close'] + premium_df['SL_close']) / 2
        premium_df = premium_df.fillna(method='ffill')
        if usdt_conversion:
            y_value = (1+premium_df['tp_close']/100) * premium_df['dollar']
            y_enter_value = (1+premium_df['LS_close']/100) * premium_df['dollar']
            y_exit_value = (1+premium_df['SL_close']/100) * premium_df['dollar']
        else:
            y_value = premium_df['tp_close']
            y_enter_value = premium_df['LS_close']
            y_exit_value = premium_df['SL_close']

        if draw_plot:
            ax.plot(premium_df['datetime_now'], y_value, marker='.', alpha=0.85, label=f'{base_asset}|{converted_market_code_combination}')
            # ax.plot(premium_df['datetime_now'], y_enter_value, marker='.', alpha=0.85, label=f'{base_asset}|{converted_market_code_combination} LS')
            # ax.plot(premium_df['datetime_now'], y_exit_value, marker='.', alpha=0.85, label=f'{base_asset}|{converted_market_code_combination} SL')
            # mpf.plot(pd.DataFrame(columns=['Open','High','Low','Close'], data=premium_df.loc[:, 'tp_open':'tp_close'].to_numpy(), index=premium_df['datetime_now'].values),type='candle', figsize=(14,10), ylabel='', ax=ax)

        timedel = premium_df['datetime_now'].iloc[-1] - premium_df['datetime_now'].iloc[-2]
        
        if draw_plot:
            ax.set_xlim(premium_df['datetime_now'].iloc[0], premium_df['datetime_now'].iloc[-1]+(timedel * 20))
            if usdt_conversion == False:
                ax.yaxis.set_major_formatter(mtick.PercentFormatter())
            ax.tick_params(labelsize=14)
            ax.tick_params(labelsize=14)
            ax.set_ylabel('Kimchi Premium', fontsize=20)
            ax.legend(prop={'size':20})
            
        # Regression Line
        clf = linear_model.LinearRegression()
        x_axis = np.array(list(range(len(y_value)))).reshape(-1,1)
        clf.fit(x_axis, y_value)
        prediction = clf.predict(x_axis)
        
        if draw_plot:
            ax.plot(premium_df['datetime_now'], prediction, color='green', alpha=0.65, linestyle='--')
            
        # extrapolate number
        extra_interval_num = 3
        linear_pred = clf.predict((x_axis[-1]+extra_interval_num).reshape(-1,1))
        if usdt_conversion == True:
            lower_bound = linear_pred-(0.5*percent_gap*0.01*linear_pred)
            upper_bound = linear_pred+(0.5*percent_gap*0.01*linear_pred)
        else:
            lower_bound = linear_pred-(0.5*percent_gap)
            upper_bound = linear_pred+(0.5*percent_gap)

        if 'T' in interval:
            extra_interval_min = int(interval.replace('T', ''))
        elif 'H' in interval:
            extra_interval_min = 60 * int(interval.replace('H', ''))
        elif 'D' in interval:
            extra_interval_min = 60 * 24 * int(interval.replace('D', ''))
        else:
            # raise error
            raise ValueError(f"Invalid interval: {interval}")
        
        lower_bound = round(float(lower_bound[0]), 3)
        upper_bound = round(float(upper_bound[0]), 3)
        
        if draw_plot:
            ax.plot((premium_df['datetime_now'].iloc[-1] + datetime.timedelta(minutes=extra_interval_min*extra_interval_num)), lower_bound, 'X', color='r', markersize = 20)
            ax.plot((premium_df['datetime_now'].iloc[-1] + datetime.timedelta(minutes=extra_interval_min*extra_interval_num)), upper_bound, 'X', color='r', markersize = 20)

        if draw_plot:
            buf = BytesIO()
            fig.savefig(buf, format='png', dpi=75, bbox_inches='tight')
            # test save as image
            plt.savefig(f"/home/trade_core/data_process/{base_asset}_plot.png", format='png', dpi=75, bbox_inches='tight')
            # plt.show()               # test
            plt.close(fig)
        else:
            buf = None
            
        output_dict = {
            "buf": buf,
            "regression_line": {"x": list(premium_df['datetime_now'].dt.strftime('%Y-%m-%dT%H:%M:%S').values), "y": list(prediction)},
            "predicted_points": {"x": [x.isoformat() for x in list(2*[premium_df['datetime_now'].iloc[-1] + datetime.timedelta(minutes=extra_interval_min*extra_interval_num)])], "y":[lower_bound, upper_bound]}
        }
        if return_dict is not None:
            return_dict['return'] = output_dict
        # Close the connection
        mongo_db_conn.close()
        return output_dict
    except Exception as e:
        logger.error(f"get_pboundary|{converted_market_code_combination}|{base_asset}|{interval}|{traceback.format_exc()}")
        raise e
