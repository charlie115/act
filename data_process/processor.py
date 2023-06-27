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
# library for candlestick
import mplfinance as mpf

# Skip any overhead related to the GUI backends.
import matplotlib
matplotlib.use('Agg')

upper_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(upper_dir)
from etc.db_handler.create_schema_tables import InitDBClient
from loggers.logger import KimpBotLogger


class InitDataProcessor:
    def __init__(self, logging_dir, remote_db_dict, kline_schema_name='coin_kimp_kline'):
        self.data_process_logger = KimpBotLogger("data_process_logger", logging_dir).logger
        self.remote_db_dict = remote_db_dict
        self.kline_schema_name = kline_schema_name

    # Deprecated
    def get_boundary_plot(self, coin, period, std_coef=1, return_dict=None):
        remote_db_dict_copy = self.remote_db_dict.copy()
        remote_db_dict_copy['database'] = self.kline_schema_name  
        too_narrow = False
        plt.clf()
        fig = plt.figure(figsize=(14,8))
        ax = plt.gca()
        ax.grid(True)

        usdt_switch = False
        if 'USDT' in coin:
            usdt_switch = True

        # Load kimp_kline from DB
        # db_start = time.time()                                                      #test
        db_client = InitDBClient(**remote_db_dict_copy)
        db_client.curr.execute("""SELECT * FROM upbit_okxf_{coin} WHERE period=%s ORDER BY datetime_kst DESC LIMIT 200""".format(coin=coin.replace('USDT','')), period)
        fetched = db_client.curr.fetchall()
        # print(f"db fetch time: {time.time() - db_start}")                           #test
        db_client.conn.close()
        upbit_okxf_df = pd.DataFrame(fetched).drop('id', axis=1).sort_values('datetime_kst').reset_index(drop=True).drop_duplicates()

        if usdt_switch:
            y_value = (1+upbit_okxf_df['okx_close_kimp']) * upbit_okxf_df['dollar']
        else:
            y_value = upbit_okxf_df['okx_close_kimp'] * 100

        latest_200_candle_std = y_value.std()
        adjusted_200_candle_std = latest_200_candle_std * std_coef

        # if the gap is too small to cover exchange fees, change it to minimum values
        if adjusted_200_candle_std <= 0.1:
            too_narrow = True
            adjusted_200_candle_std = 0.1

        ax.plot(upbit_okxf_df['datetime_kst'], y_value, marker='.', alpha=0.85, label='OKX_'+coin.upper())

        timedel = upbit_okxf_df['datetime_kst'].iloc[-1] - upbit_okxf_df['datetime_kst'].iloc[-2]
        ax.set_xlim(upbit_okxf_df['datetime_kst'].iloc[0], upbit_okxf_df['datetime_kst'].iloc[-1]+(timedel * 20))
        if usdt_switch == False:
            ax.yaxis.set_major_formatter(mtick.PercentFormatter())
        ax.tick_params(labelsize=14)
        ax.tick_params(labelsize=14)
        ax.set_ylabel('Kimchi Premium', fontsize=20)
        ax.legend(prop={'size':20})
        # Bollinger Bands
        # mbb = upbit_okxf_df['okx_close_kimp'].rolling(window).mean()
        # ubb = mbb + 2 * upbit_okxf_df['okx_close_kimp'].rolling(window).std()
        # lbb = mbb - 2 * upbit_okxf_df['okx_close_kimp'].rolling(window).std()
        # ax.plot(upbit_okxf_df['datetime_kst'], ubb*100, alpha=0.5, linewidth=0.65)
        # ax.plot(upbit_okxf_df['datetime_kst'], mbb*100, alpha=0.5, linewidth=0.65)
        # ax.plot(upbit_okxf_df['datetime_kst'], lbb*100, alpha=0.5, linewidth=0.65)
        # Regression Line
        clf = linear_model.LinearRegression()
        x_axis = np.array(list(range(len(y_value)))).reshape(-1,1)
        clf.fit(x_axis, y_value)
        ax.plot(upbit_okxf_df['datetime_kst'], clf.predict(x_axis), color='green', alpha=0.65, linestyle='--')

        # extrapolate number
        extra_min_num = 3
        linear_pred = clf.predict((x_axis[-1]+extra_min_num).reshape(-1,1))
        lower_bound = linear_pred-adjusted_200_candle_std
        upper_bound = linear_pred+adjusted_200_candle_std

        ax.plot((upbit_okxf_df['datetime_kst'].iloc[-1] + datetime.timedelta(minutes=extra_min_num)), lower_bound, 'X', color='r', markersize = 20)
        ax.plot((upbit_okxf_df['datetime_kst'].iloc[-1] + datetime.timedelta(minutes=extra_min_num)), upper_bound, 'X', color='r', markersize = 20)
        # ax.axhline(y=lower_bound*100, xmin=0.25, color='r', linestyle=':')
        # ax.axhline(y=upper_bound*100, xmin=0.25, color='r', linestyle=':')

        buf = BytesIO()
        fig.savefig(buf, format='png', dpi=75, bbox_inches='tight')
        # plt.show()               # test
        plt.close(fig)
        if return_dict is not None:
            return_dict['return'] = (buf, lower_bound, upper_bound, too_narrow)
        return buf, lower_bound, upper_bound, too_narrow

    def get_pboundary_plot(self, coin, period, percent_gap, return_dict=None):
        try:
            remote_db_dict_copy = self.remote_db_dict.copy()
            remote_db_dict_copy['database'] = self.kline_schema_name
            plt.clf()
            fig = plt.figure(figsize=(14,8))
            ax = plt.gca()
            ax.grid(True)

            usdt_switch = False
            if 'USDT' in coin:
                usdt_switch = True

            # Load kimp_kline from DB
            # db_start = time.time()                                                      #test
            db_client = InitDBClient(**remote_db_dict_copy)
            db_client.curr.execute("""SELECT * FROM upbit_okxf_{coin} WHERE period=%s ORDER BY datetime_kst DESC LIMIT 200""".format(coin=coin.replace('USDT','')), period)
            fetched = db_client.curr.fetchall()
            # print(f"db fetch time: {time.time() - db_start}")                           #test
            db_client.conn.close()
            upbit_okxf_df = pd.DataFrame(fetched).drop('id', axis=1).sort_values('datetime_kst').reset_index(drop=True).drop_duplicates()

            if usdt_switch:
                y_value = (1+upbit_okxf_df['okx_close_kimp']) * upbit_okxf_df['dollar']
            else:
                y_value = upbit_okxf_df['okx_close_kimp'] * 100

            ax.plot(upbit_okxf_df['datetime_kst'], y_value, marker='.', alpha=0.85, label='OKX_'+coin.upper())

            timedel = upbit_okxf_df['datetime_kst'].iloc[-1] - upbit_okxf_df['datetime_kst'].iloc[-2]
            ax.set_xlim(upbit_okxf_df['datetime_kst'].iloc[0], upbit_okxf_df['datetime_kst'].iloc[-1]+(timedel * 20))
            if usdt_switch == False:
                ax.yaxis.set_major_formatter(mtick.PercentFormatter())
            ax.tick_params(labelsize=14)
            ax.tick_params(labelsize=14)
            ax.set_ylabel('Kimchi Premium', fontsize=20)
            ax.legend(prop={'size':20})
            # Bollinger Bands
            # mbb = upbit_okxf_df['okx_close_kimp'].rolling(window).mean()
            # ubb = mbb + 2 * upbit_okxf_df['okx_close_kimp'].rolling(window).std()
            # lbb = mbb - 2 * upbit_okxf_df['okx_close_kimp'].rolling(window).std()
            # ax.plot(upbit_okxf_df['datetime_kst'], ubb*100, alpha=0.5, linewidth=0.65)
            # ax.plot(upbit_okxf_df['datetime_kst'], mbb*100, alpha=0.5, linewidth=0.65)
            # ax.plot(upbit_okxf_df['datetime_kst'], lbb*100, alpha=0.5, linewidth=0.65)
            # Regression Line
            clf = linear_model.LinearRegression()
            x_axis = np.array(list(range(len(y_value)))).reshape(-1,1)
            clf.fit(x_axis, y_value)
            ax.plot(upbit_okxf_df['datetime_kst'], clf.predict(x_axis), color='green', alpha=0.65, linestyle='--')

            # extrapolate number
            extra_min_num = 3
            linear_pred = clf.predict((x_axis[-1]+extra_min_num).reshape(-1,1))
            if usdt_switch == True:
                lower_bound = linear_pred-(0.5*percent_gap*0.01*linear_pred)
                upper_bound = linear_pred+(0.5*percent_gap*0.01*linear_pred)
            else:
                lower_bound = linear_pred-(0.5*percent_gap)
                upper_bound = linear_pred+(0.5*percent_gap)

            ax.plot((upbit_okxf_df['datetime_kst'].iloc[-1] + datetime.timedelta(minutes=extra_min_num)), lower_bound, 'X', color='r', markersize = 20)
            ax.plot((upbit_okxf_df['datetime_kst'].iloc[-1] + datetime.timedelta(minutes=extra_min_num)), upper_bound, 'X', color='r', markersize = 20)
            # ax.axhline(y=lower_bound*100, xmin=0.25, color='r', linestyle=':')
            # ax.axhline(y=upper_bound*100, xmin=0.25, color='r', linestyle=':')

            buf = BytesIO()
            fig.savefig(buf, format='png', dpi=75, bbox_inches='tight')
            # plt.show()               # test
            plt.close(fig)
            lower_bound = round(float(lower_bound[0]), 3)
            upper_bound = round(float(upper_bound[0]), 3)
            if return_dict is not None:
                return_dict['return'] = (buf, lower_bound, upper_bound)
            return buf, lower_bound, upper_bound
        except Exception:
            self.data_process_logger.error(f"get_pboundary_plot|{traceback.format_exc()}")

    def get_plot(self, coin_list, period, detail=False, compare_usdt_kp=False, window=9, return_dict=None):
        try:
            remote_db_dict_copy = self.remote_db_dict.copy()
            remote_db_dict_copy['database'] = self.kline_schema_name

            plt.clf()
            fig = plt.figure(figsize=(14,8))

            usdt_switch = False
            for each_coin in coin_list:
                if 'USDT' in each_coin:
                    usdt_switch = True

            if compare_usdt_kp:
                detail = True

            if not detail and usdt_switch == False:
                plt.axhline(y=0, color = 'r', linestyle='--', alpha=0.5)
        
            if len(coin_list) == 1:
                ax = plt.gca()
                ax.grid(True)
                if not detail or compare_usdt_kp == True:
                    ax2 = ax.twinx()

                for coin in coin_list:
                    # Load kimp_kline from DB
                    db_client = InitDBClient(**remote_db_dict_copy)
                    db_client.curr.execute("""SELECT * FROM upbit_okxf_{coin} WHERE period=%s ORDER BY datetime_kst DESC LIMIT 200""".format(coin=coin.replace('USDT','')), period)
                    fetched = db_client.curr.fetchall()
                    db_client.conn.close()
                    upbit_okxf_df = pd.DataFrame(fetched).drop('id', axis=1).sort_values('datetime_kst').reset_index(drop=True)

                    if usdt_switch:
                        y_value = upbit_okxf_df['dollar'] * (1 + upbit_okxf_df['okx_close_kimp'])
                    else:
                        y_value = upbit_okxf_df['okx_close_kimp'] * 100

                    # ax.plot(upbit_okxf_df['datetime_kst'], 100 * upbit_okxf_df['okx_close_kimp'], marker='.', alpha=0.85, label='OKX_'+coin.upper())
                    ax.plot(upbit_okxf_df['datetime_kst'], y_value, marker='.', alpha=0.85, label='OKX_'+coin.upper())
                    if not detail:
                        ax2.plot(upbit_okxf_df['datetime_kst'], upbit_okxf_df['okx_close'].astype('float'), color='r', alpha=0.3, label=f"{coin.upper().replace('USDT','')}USDT Price USD")
                        ax2.legend(prop={'size':15}, loc=4)
                    if compare_usdt_kp:
                        ax2.plot(upbit_okxf_df['datetime_kst'], upbit_okxf_df['okx_close_kimp'] * 100, color='r', alpha=0.3, label=f"{coin.upper().replace('USDT','')} Kimp")
                        ax2.legend(prop={'size':15}, loc=4)
                        ax2.yaxis.set_major_formatter(mtick.PercentFormatter())
                        ax2.set_ylabel("Kimp", fontsize=20)

                timedel = upbit_okxf_df['datetime_kst'].iloc[-1] - upbit_okxf_df['datetime_kst'].iloc[-2]
                ax.set_xlim(upbit_okxf_df['datetime_kst'].iloc[0], upbit_okxf_df['datetime_kst'].iloc[-1]+(timedel * 10))
                if usdt_switch == False:
                    ax.yaxis.set_major_formatter(mtick.PercentFormatter())
                    ax.set_ylabel('Kimp', fontsize=20)
                else:
                    ax.set_ylabel('Tether Kimp', fontsize=20)            
                ax.tick_params(labelsize=14)
                ax.tick_params(labelsize=14)
                ax.legend(prop={'size':20})
                # Bollinger Bands
                # mbb = upbit_okxf_df['okx_close_kimp'].rolling(window).mean()
                # ubb = mbb + 2 * upbit_okxf_df['okx_close_kimp'].rolling(window).std()
                # lbb = mbb - 2 * upbit_okxf_df['okx_close_kimp'].rolling(window).std()
                # ax.plot(upbit_okxf_df['datetime_kst'], ubb*100, alpha=0.5, linewidth=0.65)
                # ax.plot(upbit_okxf_df['datetime_kst'], mbb*100, alpha=0.5, linewidth=0.65)
                # ax.plot(upbit_okxf_df['datetime_kst'], lbb*100, alpha=0.5, linewidth=0.65)
                mbb = y_value.rolling(window).mean()
                ubb = mbb + 2 * y_value.rolling(window).std()
                lbb = mbb - 2 * y_value.rolling(window).std()
                ax.plot(upbit_okxf_df['datetime_kst'], ubb, alpha=0.5, linewidth=0.65)
                ax.plot(upbit_okxf_df['datetime_kst'], mbb, alpha=0.5, linewidth=0.65)
                ax.plot(upbit_okxf_df['datetime_kst'], lbb, alpha=0.5, linewidth=0.65)
                # Regression Line
                clf = linear_model.LinearRegression()
                # x_axis = np.array(list(range(len(upbit_okxf_df['okx_close_kimp'])))).reshape(-1,1)
                # clf.fit(x_axis, upbit_okxf_df['okx_close_kimp'])
                # ax.plot(upbit_okxf_df['datetime_kst'], clf.predict(x_axis)*100, color='green', alpha=0.65, linestyle='--')
                x_axis = np.array(list(range(len(y_value)))).reshape(-1,1)
                clf.fit(x_axis, y_value)
                ax.plot(upbit_okxf_df['datetime_kst'], clf.predict(x_axis), color='green', alpha=0.65, linestyle='--')
            
            else:
                plt.grid(True)
                for coin in coin_list:
                    # Load kimp_kline from DB
                    db_client = InitDBClient(**remote_db_dict_copy)
                    db_client.curr.execute("""SELECT * FROM upbit_okxf_{coin} WHERE period=%s ORDER BY datetime_kst DESC LIMIT 200""".format(coin=coin.replace('USDT','')), period)
                    fetched = db_client.curr.fetchall()
                    db_client.conn.close()
                    upbit_okxf_df = pd.DataFrame(fetched).drop('id', axis=1).sort_values('datetime_kst')

                    # test
                    if usdt_switch:
                        y_value = upbit_okxf_df['dollar'] * (1 + upbit_okxf_df['okx_close_kimp'])
                    else:
                        y_value = upbit_okxf_df['okx_close_kimp'] * 100
                    # test

                    plt.plot(upbit_okxf_df['datetime_kst'], y_value, marker='.', alpha=0.85, label='OKX_'+coin.upper())

                timedel = upbit_okxf_df['datetime_kst'].iloc[-1] - upbit_okxf_df['datetime_kst'].iloc[-2]
                plt.gca().set_xlim(upbit_okxf_df['datetime_kst'].iloc[0], upbit_okxf_df['datetime_kst'].iloc[-1]+(timedel * 10))
                if usdt_switch == False:
                    plt.gca().yaxis.set_major_formatter(mtick.PercentFormatter())
                plt.yticks(fontsize=14)
                plt.xticks(fontsize=14)
                plt.ylabel('Kimchi Premium', fontsize=20)
                plt.legend(prop={'size':25})

            buf = BytesIO()
            fig.savefig(buf, format='png', dpi=75, bbox_inches='tight')
            plt.close(fig)
            if return_dict is not None:
                return_dict['return'] = buf
            return buf
        except:
            self.data_process_logger.error(f"get_plot|{traceback.format_exc()}")

    def get_plotc(self, coin, period, detail=False, window=9, return_dict=None):
        try:
            remote_db_dict_copy = self.remote_db_dict.copy()
            remote_db_dict_copy['database'] = self.kline_schema_name

            plt.clf()
            fig = plt.figure(figsize=(14,8))

            usdt_switch = False
            if 'USDT' in coin:
                usdt_switch = True

            if not detail and usdt_switch == False:
                plt.axhline(y=0, color = 'r', linestyle='--', alpha=0.25)
            
            # Load kimp_kiline from DB
            db_client = InitDBClient(**remote_db_dict_copy)
            db_client.curr.execute("""SELECT * FROM upbit_okxf_{coin} WHERE period=%s ORDER BY datetime_kst DESC LIMIT 200""".format(coin=coin.upper().replace('USDT','')), period)
            fetched = db_client.curr.fetchall()
            db_client.conn.close()
            upbit_okxf_df = pd.DataFrame(fetched).drop('id', axis=1).sort_values('datetime_kst').reset_index(drop=True)

            # test
            if usdt_switch:
                y_df = (1+upbit_okxf_df.loc[:, 'okx_open_kimp':'okx_close_kimp']).multiply(upbit_okxf_df['dollar'], axis=0)
                y_value = y_df.to_numpy()
            else:
                y_df = (upbit_okxf_df.loc[:, 'okx_open_kimp':'okx_close_kimp'] * 100)
                y_value = y_df.to_numpy()
            # test

            # Preprocess
            index = upbit_okxf_df['datetime_kst'].values

            # # Preprocess
            # index = upbit_okxf_df['datetime_kst'].values
            # kimp_array = upbit_okxf_df.loc[:, 'okx_open_kimp':'okx_close_kimp'].to_numpy()

            ax = plt.gca()
            ax.grid(True)
            if not detail:
                ax2 = ax.twinx()
                ax2.grid(False)

            mpf.plot(pd.DataFrame(columns=['Open','High','Low','Close'], data=y_value, index=index),type='candle', figsize=(14,10), style='okx', ylabel='', ax=ax)

            if usdt_switch == False:
                ax.yaxis.set_major_formatter(mtick.PercentFormatter())
                ax.set_title(f'OKX_{coin.upper()}USDT Kimp')
            else:
                ax.set_title(f'OKX_{coin.upper()}USDT Tether Kimp')
            ax.tick_params(labelsize=12)
            
            if not detail:
                ax2.plot((upbit_okxf_df[f'okx_open_krw']/upbit_okxf_df['dollar']), alpha=0.2, color='r', label=f"OKX_{coin.upper().replace('USDT','')}USDT_USD")
                ax2.legend(prop={'size':10})
            # Bollinger Bands
            mbb = y_df['okx_close_kimp'].rolling(window).mean()
            ubb = mbb + 2 * y_df['okx_close_kimp'].rolling(window).std()
            lbb = mbb - 2 * y_df['okx_close_kimp'].rolling(window).std()
            ax.plot(ubb, alpha=0.5, linewidth=0.65)
            ax.plot(mbb, alpha=0.5, linewidth=0.65)
            ax.plot(lbb, alpha=0.5, linewidth=0.65)
            # regression line
            clf = linear_model.LinearRegression()
            x_axis = np.array(list(range(len(y_df['okx_close_kimp'])))).reshape(-1,1)
            clf.fit(x_axis, y_df['okx_close_kimp'])
            ax.plot(clf.predict(x_axis), color='green', alpha=0.65, linestyle='--')

            buf = BytesIO()
            fig.savefig(buf, format='png', dpi=75, bbox_inches='tight')
            plt.close(fig)
            # plt.show()
            if return_dict is not None:
                return_dict['return'] = buf
            return buf
        except:
            self.data_process_logger.error(f"get_plotc|{traceback.format_exc()}")

    def calculate_profit(self, redis_uuid, trade_history_df):
        try:
            concise_cols = ['user_id','datetime','symbol','addcoin_redis_uuid','dollar','okx_side','upbit_price','upbit_qty','okx_price','okx_qty','executed_kimp']
            redis_uuid_trade_history_df = trade_history_df[trade_history_df['addcoin_redis_uuid']==redis_uuid][concise_cols]
            redis_uuid_trade_history_df['upbit_enter_krw'] = redis_uuid_trade_history_df.apply(lambda x: None if x['okx_side'].upper()=='BUY' else x['upbit_price']*x['upbit_qty'], axis=1)
            redis_uuid_trade_history_df['okx_enter'] = redis_uuid_trade_history_df.apply(lambda x: None if x['okx_side'].upper()=='BUY' else x['okx_price']*x['okx_qty'], axis=1)
            redis_uuid_trade_history_df['upbit_exit_krw'] = redis_uuid_trade_history_df.apply(lambda x: None if x['okx_side'].upper()=='SELL' else x['upbit_price']*x['upbit_qty'], axis=1)
            redis_uuid_trade_history_df['okx_exit'] = redis_uuid_trade_history_df.apply(lambda x: None if x['okx_side'].upper()=='SELL' else x['okx_price']*x['okx_qty'], axis=1)
            i = 0
            for row_tup in redis_uuid_trade_history_df.iterrows():
                index = row_tup[0]
                row = row_tup[1]
                symbol = row['symbol']
                dollar = row['dollar']
                upbit_qty = row['upbit_qty']
                okx_qty = row['okx_qty']
                executed_kimp = row['executed_kimp']
                if row['okx_side'].upper() == 'SELL':
                    kimp_side = 'enter'
                else:
                    kimp_side = 'exit'
                
                if kimp_side == 'enter':
                    i += 1
                    prev_upbit_qty = upbit_qty
                    prev_okx_qty = okx_qty
                    upbit_enter_krw = row['upbit_enter_krw']
                    upbit_enter_fee = upbit_enter_krw * 0.0005
                    okx_enter = row['okx_enter']
                    okx_enter_fee = okx_enter * 0.0004
                
                if i != 0 and kimp_side == 'exit' and prev_upbit_qty == upbit_qty and prev_okx_qty == okx_qty:
                    upbit_exit_krw = row['upbit_exit_krw']
                    upbit_exit_fee = upbit_exit_krw * 0.0005
                    upbit_total_fee = upbit_enter_fee + upbit_exit_fee
                    okx_exit = row['okx_exit']
                    okx_exit_fee = okx_exit * 0.0004
                    okx_total_fee = okx_enter_fee + okx_exit_fee

                    upbit_pnl_after_fee = upbit_exit_krw - upbit_enter_krw - upbit_total_fee
                    okx_pnl_after_fee = -(okx_exit - okx_enter) - okx_total_fee

                    redis_uuid_trade_history_df.loc[index, 'upbit_pnl'] = upbit_exit_krw - upbit_enter_krw
                    redis_uuid_trade_history_df.loc[index, 'upbit_fee'] = upbit_total_fee
                    redis_uuid_trade_history_df.loc[index, 'okx_pnl'] = -(okx_exit - okx_enter)
                    redis_uuid_trade_history_df.loc[index, 'okx_fee'] = okx_total_fee
                    redis_uuid_trade_history_df.loc[index, 'profit_krw_after_fee'] = upbit_pnl_after_fee + okx_pnl_after_fee*dollar
                    redis_uuid_trade_history_df.loc[index, 'profit_krw_after_fee_and_kimp'] = upbit_pnl_after_fee + okx_pnl_after_fee*dollar*(1+executed_kimp)
            return redis_uuid_trade_history_df
        except Exception as e:
            self.data_process_logger.error(f"Error occured in calculated_profit func redis_uuid: {redis_uuid}, {traceback.format_exc()}")

    def user_profit(self, start_time, end_time, user_id, trade_history_df):
        try:
            filtered_trade_history_df = trade_history_df[trade_history_df['datetime'].between(start_time,end_time)]
            user_trade_history_df = filtered_trade_history_df[filtered_trade_history_df['user_id']==user_id]
            user_redis_uuid_list = list(set(user_trade_history_df.dropna(subset=['addcoin_redis_uuid'])['addcoin_redis_uuid'].to_list()))
            if len(user_trade_history_df) == 0:
                print(f"user_trade_history_df is empty!")
                return pd.DataFrame(), 0
            for i, redis_uuid in enumerate(user_redis_uuid_list):
                if i == 0:
                    merged_df = pd.DataFrame()
                # print(redis_uuid)
                merged_df = merged_df.append(self.calculate_profit(redis_uuid, user_trade_history_df), ignore_index=True)
            merged_df = merged_df.sort_values('datetime')
            okx_trade_sum = merged_df['okx_enter'].sum() + merged_df['okx_exit'].sum()

            return merged_df, okx_trade_sum
        except Exception as e:
            self.data_process_logger.error(f"Error occured in user_profit func redis_uuid: {redis_uuid}, {traceback.format_exc()}")

    def get_user_profit_df(self, user_id, days, trade_history_df):
        try:
            whole_end_time = datetime.datetime.now()
            whole_start_time = whole_end_time - datetime.timedelta(days=days)
            merged_df, okx_trade_sum = self.user_profit(whole_start_time, whole_end_time, user_id, trade_history_df)
            if len(merged_df) == 0 or 'profit_krw_after_fee' not in merged_df.columns:
                return pd.DataFrame(), pd.DataFrame()
            else:
                merged_df['date'] = merged_df['datetime'].apply(lambda x: x.date())
                profit_per_day_df = merged_df.groupby('date')[['profit_krw_after_fee']].agg('sum').round()
                profit_per_day_df = profit_per_day_df.reindex(pd.date_range(start=whole_start_time.date(), end=whole_end_time.date(), freq='1D')).fillna(0)
                profit_per_day_df['profit_krw_cum'] = profit_per_day_df['profit_krw_after_fee'].cumsum()
                profit_per_day_df = profit_per_day_df.sort_index(ascending=False)
                merged_df = merged_df.dropna(subset=['profit_krw_after_fee']).sort_values('datetime', ascending=False).reset_index(drop=True)
                return profit_per_day_df, merged_df
        except Exception:
            self.data_process_logger.error(f"Error occured in get_user_profit_df func, {traceback.format_exc()}")

    # Fetch kimp standard deviation
    def calculate_kimp_std(self, symbol_list, datetime_start, period=1, return_dict=None):
        try:
            remote_db_dict_copy = self.remote_db_dict.copy()
            remote_db_dict_copy['database'] = self.kline_schema_name

            datetime_start_str = datetime.datetime.strftime(datetime_start, "%Y-%m-%d %H:%M")
            db_client = InitDBClient(**remote_db_dict_copy)
            kimp_std_dict = {}
            # start = time.time()                 # test
            for symbol in symbol_list:
                try:
                    db_client.curr.execute("""SELECT * FROM upbit_okxf_{table} WHERE datetime_kst>'{date}' AND period=%s""".format(table=symbol, date=datetime_start_str), period)
                    fetched_df = pd.DataFrame(db_client.curr.fetchall()).drop('id', axis=1)
                    kimp_std = fetched_df['okx_close_kimp'].std()
                    kimp_std_dict[symbol] = kimp_std
                except Exception as e:
                    self.data_process_logger.error(f"calculate_kimp_std| Error occured while processing {symbol} {traceback.format_exc()}")
            db_client.conn.close()
            # print(time.time()-start)            # test
            kimp_std_df = pd.DataFrame(kimp_std_dict, index=[0]).transpose().sort_values(0, ascending=False).reset_index()
            kimp_std_df = kimp_std_df.rename(columns={'index':'symbol', 0:'kimp_std'})

            if return_dict is None:
                return kimp_std_df
            else:
                return_dict['res'] = kimp_std_df
        except:
            self.data_process_logger.error(f"calculate_kimp_std|{traceback.format_exc()}")
