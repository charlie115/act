import sys
import os
import datetime
import traceback
import pandas as pd
import time
from okx.Account import AccountAPI
from okx.BlockTrading import BlockTradingAPI
from okx.Convert import ConvertAPI
from okx.Earning import EarningAPI
from okx.FDBroker import FDBrokerAPI
from okx.Funding import FundingAPI
from okx.Grid import GridAPI
from okx.MarketData import MarketAPI
from okx.NDBroker import NDBrokerAPI
from okx.PublicData import PublicAPI
from okx.Status import StatusAPI
from okx.SubAccount import SubAccountAPI
from okx.Trade import TradeAPI
from okx.TradingData import TradingDataAPI

upper_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(upper_dir)
from loggers.logger import KimpBotLogger

class OkxClient:
    def __init__(self, okx_api_key='-1', okx_secret_key='-1', passphrase='-1', demo_trading='0', debug=False):
        self.okx_api_key = okx_api_key
        self.okx_secret_key = okx_secret_key
        self.passphrase = passphrase
        self.AccountAPI = AccountAPI(api_key=okx_api_key, api_secret_key=okx_secret_key, passphrase=passphrase, flag=demo_trading, debug=debug)
        self.BlockTradingAPI = BlockTradingAPI(api_key=okx_api_key, api_secret_key=okx_secret_key, passphrase=passphrase, flag=demo_trading, debug=debug)
        self.ConvertAPI = ConvertAPI(api_key=okx_api_key, api_secret_key=okx_secret_key, passphrase=passphrase, flag=demo_trading, debug=debug)
        self.EarningAPI = EarningAPI(api_key=okx_api_key, api_secret_key=okx_secret_key, passphrase=passphrase, flag=demo_trading, debug=debug)
        self.FDBrokerAPI = FDBrokerAPI(api_key=okx_api_key, api_secret_key=okx_secret_key, passphrase=passphrase, flag=demo_trading, debug=debug)
        self.FundingAPI = FundingAPI(api_key=okx_api_key, api_secret_key=okx_secret_key, passphrase=passphrase, flag=demo_trading, debug=debug)
        self.GridAPI = GridAPI(api_key=okx_api_key, api_secret_key=okx_secret_key, passphrase=passphrase, flag=demo_trading, debug=debug)
        self.MarketAPI = MarketAPI(api_key=okx_api_key, api_secret_key=okx_secret_key, passphrase=passphrase, flag=demo_trading, debug=debug)
        self.NDBrokerAPI = NDBrokerAPI(api_key=okx_api_key, api_secret_key=okx_secret_key, passphrase=passphrase, flag=demo_trading, debug=debug)
        self.PublicAPI = PublicAPI(api_key=okx_api_key, api_secret_key=okx_secret_key, passphrase=passphrase, flag=demo_trading, debug=debug)
        self.StatusAPI = StatusAPI(api_key=okx_api_key, api_secret_key=okx_secret_key, passphrase=passphrase, flag=demo_trading, debug=debug)
        self.SubAccountAPI = SubAccountAPI(api_key=okx_api_key, api_secret_key=okx_secret_key, passphrase=passphrase, flag=demo_trading, debug=debug)
        self.TradeAPI = TradeAPI(api_key=okx_api_key, api_secret_key=okx_secret_key, passphrase=passphrase, flag=demo_trading, debug=debug)
        self.TradingDataAPI = TradingDataAPI(api_key=okx_api_key, api_secret_key=okx_secret_key, passphrase=passphrase, flag=demo_trading, debug=debug)

class InitOkxAdaptor:
    def __init__(self, read_only_okx_access_key='-1', read_only_okx_secret_key='-1', passphrase='-1', demo_trading='0', debug=False, logging_dir=None):
        self.demo_trading = demo_trading
        self.my_okx_client = OkxClient(okx_api_key=read_only_okx_access_key, okx_secret_key=read_only_okx_secret_key, passphrase=passphrase, demo_trading=demo_trading, debug=debug)
        self.pub_okx_client = OkxClient()
        self.user_client_dict = {}
        self.okx_plug_logger = KimpBotLogger("okx_plug", logging_dir).logger
        self.retry_term_sec = 0.2
        self.retry_count_limit = 2
        self.okx_plug_logger.info(f"okx_plug_logger started.")
        self.instrument_info = self.get_instrument_info()

    def get_instrument_info(self):
        result = pd.DataFrame(self.pub_okx_client.PublicAPI.get_instruments(instType='SWAP')['data'])[['instId','ctVal','lever','maxMktSz','minSz','state','tickSz']]
        result.loc[:, 'maxMktSz'] = result['maxMktSz'].astype(float)
        result['minQty'] = result['ctVal'].astype(float) * result['minSz'].astype(float)
        result['maxQty'] = result['ctVal'].astype(float) * result['maxMktSz'].astype(float)
        result = result[result['instId'].str.endswith('-USDT-SWAP')].reset_index(drop=True)
        return result

    def get_max_qty(self, inst_id):
        return self.instrument_info[self.instrument_info['instId'] == inst_id]['maxQty'].values[0]

    def get_min_qty(self, inst_id):
        return self.instrument_info[self.instrument_info['instId'] == inst_id]['minQty'].values[0]

    def convert_qty_to_sz(self, inst_id, qty):
        converted_sz = qty / float(self.instrument_info[self.instrument_info['instId'] == inst_id]['ctVal'].values[0])
        return converted_sz

    def convert_to_okx_perp_inst_id(self, symbol):
        return f"{symbol}-USDT-SWAP"

    def load_user_client(self, user_okx_access_key, user_okx_secret_key, passphrase):
        user_client = self.user_client_dict.get(user_okx_access_key)
        if user_client is None:
            self.user_client_dict[user_okx_access_key] = OkxClient(user_okx_access_key, user_okx_secret_key, passphrase, self.demo_trading)
            return self.user_client_dict[user_okx_access_key]
        else:
            return user_client

    # Admin
    def get_deposit(self, asset='EOS'):
        deposit = pd.DataFrame(self.my_okx_client.FundingAPI.get_deposit_history(ccy=asset)['data'])
        if len(deposit) == 0:
            print(f'No deposit history for {asset}')
            return deposit
        else:
            deposit.loc[:, 'insertTime'] = deposit['ts'].astype(float).apply(lambda x: datetime.datetime.fromtimestamp(x/1000))
            deposit.loc[:, 'amount'] = deposit['amt'].astype(float)
            return deposit

    def check_okx_api_key(self, user_okx_access_key, user_okx_secret_key, passphrase):
        self.user_client_dict.pop(user_okx_access_key, None)
        try:
            self.get_okx_trade_balance(user_okx_access_key, user_okx_secret_key, passphrase)
            return (True, 'OK')
        except Exception as e:
            self.user_client_dict.pop(user_okx_access_key, None)
            return (False, str(e))

    def get_okx_funding_balance(self, user_okx_access_key, user_okx_secret_key, passphrase):
        okx_client = self.load_user_client(user_okx_access_key, user_okx_secret_key, passphrase)
        funding_balance = pd.DataFrame(okx_client.FundingAPI.get_balances()['data'])
        if len(funding_balance) != 0:
            funding_balance[:, 'availBal'] = funding_balance[:, 'availBal'].astype(float)
            funding_balance[:, 'bal'] = funding_balance[:, 'bal'].astype(float)
            funding_balance[:, 'frozenBal'] = funding_balance[:, 'frozenBal'].astype(float)
        else:
            # Make a dummy dataframe having the same columns as funding_balance
            funding_balance = pd.DataFrame(columns=['availBal', 'bal', 'ccy', 'frozenBal'])
        return funding_balance

    def get_okx_trade_balance(self, user_okx_access_key, user_okx_secret_key, passphrase, return_dict=None):
        okx_client = self.load_user_client(user_okx_access_key, user_okx_secret_key, passphrase)
        trade_balance = pd.DataFrame(okx_client.AccountAPI.get_account_balance()['data'][0]['details'])
        trade_balance.loc[:, ['availBal', 'cashBal', 'disEq', 'fixedBal', 'frozenBal']] = trade_balance[['availBal', 'cashBal', 'disEq', 'fixedBal', 'frozenBal']].astype(float)
        trade_balance_columns = ['availBal', 'availEq', 'cashBal', 'ccy', 'crossLiab', 'disEq', 'eq', 'eqUsd', 'fixedBal', 'frozenBal', 'interest', 'isoEq', 'isoLiab', 'isoUpl', 'liab', 
                   'maxLoan', 'mgnRatio', 'notionalLever', 'ordFrozen', 'spotInUseAmt', 'stgyEq', 'twap', 'uTime', 'upl', 'uplLiab']
        # if length of trade_balance is 0, make a dummy dataframe having the same columns as trade_balance
        if len(trade_balance) == 0:
            trade_balance = pd.DataFrame(columns=trade_balance_columns)
        else:
            trade_balance.loc[:, ['availBal', 'eq', 'availEq', 'upl', 'isoEq', 'mgnRatio', 'frozenBal']] = trade_balance[['availBal', 'eq', 'availEq', 'upl', 'isoEq', 'mgnRatio', 'frozenBal']].astype(float)
        if return_dict is None:
            return trade_balance
        else:
            return_dict['res'] = trade_balance

    # okx_future ordre functions
    def okx_change_position_mode(self, user_okx_access_key, user_okx_secret_key, passphrase):
        okx_client = self.load_user_client(user_okx_access_key, user_okx_secret_key, passphrase)
        res = okx_client.AccountAPI.set_position_mode('net_mode')['data'][0]
        return res

    def okx_change_leverage(self, user_okx_access_key, user_okx_secret_key, passphrase, symbol, leverage, mgnMode):
        okx_client = self.load_user_client(user_okx_access_key, user_okx_secret_key, passphrase)
        try:
            res = okx_client.AccountAPI.set_leverage(lever=leverage, mgnMode=mgnMode, instId=symbol)['data'][0]
            res['sCode'] = "0"
            res['leverage'] = res['lever']
        except Exception as e:
            res = {}
            res['sCode'] = "-1"
            res['sMsg'] = traceback.format_exc()
            self.okx_plug_logger.error(f"okx_change_leverage|{symbol}|{leverage}|{mgnMode}|{res['sMsg']}")
        return res

    def okx_order_info(self, user_okx_access_key, user_okx_secret_key, passphrase, symbol, ordId, return_dict=None):
        okx_client = self.load_user_client(user_okx_access_key, user_okx_secret_key, passphrase)
        raw_res = okx_client.TradeAPI.get_order(instId=symbol, ordId=ordId)
        state = 'OK'
        try:
            if raw_res['data'] == []:
                state = 'ERROR'
                res = {}
                res['sCode'] = "-1"
                res['sMsg'] = raw_res
                self.okx_plug_logger.error(f"okx_order_info|{symbol}|{ordId}|{raw_res}")
            else:
                res = raw_res['data'][0]
                res['sCode'] = "0"
                # print(f"res['accFillSz']: {res['accFillSz']}")
                ctVal = float(self.instrument_info[self.instrument_info['instId'] == symbol]['ctVal'].values[0])
                res['executedQty'] = float(res['accFillSz']) * ctVal
                res['qty'] = float(res['sz']) * ctVal
        except Exception as e:
            state = 'ERROR'
            res = {}
            res['sCode'] = "-1"
            res['sMsg'] = traceback.format_exc()
            self.okx_plug_logger.error(f"okx_order_info|{symbol}|{ordId}|{res['sMsg']}")
        if return_dict is not None:
            return_dict['res'] = res
            return_dict['state'] = state
        return res

    def okx_market_enter(self, user_okx_access_key, user_okx_secret_key, passphrase, symbol, qty, mgnMode, return_dict=None):
        okx_client = self.load_user_client(user_okx_access_key, user_okx_secret_key, passphrase)

        # retry_count = 0

        # while retry_count <= self.retry_count_limit:
        #     if retry_count >= 1:
        #         self.binance_plug_logger.info(f"binance_market_enter|retry_count: {retry_count}, retry_term_sec: {self.retry_term_sec}, retry_count_limit: {self.retry_count_limit}") # For TESTING
        #     try:
        #         res = bi_client.futures_create_order(
        #             symbol=symbol,
        #             side='SELL',
        #             type='MARKET',
        #             quantity=qty,
        #             recvWindow=self.recvWindow
        #         )
        #         if return_dict is not None:
        #             return_dict['res'] = res
        #             return_dict['state'] = 'OK'
        #         return res
        #     except Exception as e:
        #         if e.code not in [-1000, -1001] or retry_count == self.retry_count_limit:
        #             if return_dict is None:
        #                 raise e
        #             else:
        #                 return_dict['res'] = e
        #                 return_dict['state'] = 'ERROR'
        #                 return
        #     retry_count += 1
        try:
            res = okx_client.TradeAPI.place_order(symbol, mgnMode, 'sell', 'market', self.convert_qty_to_sz(symbol, qty))['data'][0]
        except Exception as e:
            res = {}
            res['sCode'] = "-1"
            res['sMsg'] = traceback.format_exc()
            self.okx_plug_logger.error(f"okx_market_enter|{symbol}|{qty}|{traceback.format_exc()}")
        if return_dict is not None:
            return_dict['res'] = res
            if res['sCode'] == "0":
                return_dict['state'] = 'OK'
            else:
                return_dict['state'] = 'ERROR'
        return res

    # # Original
    # def binance_market_exit(self, user_binance_access_key, user_binance_secret_key, symbol, qty, return_dict=None):
    #     bi_client = self.load_user_client(user_binance_access_key, user_binance_secret_key)
    #     if return_dict is None:
    #         res = bi_client.futures_create_order(
    #             symbol=symbol,
    #             side='BUY',
    #             type='MARKET',
    #             quantity=qty,
    #             recvWindow=self.recvWindow
    #         )
    #         return res
    #     else:
    #         try:
    #             return_dict['res'] = bi_client.futures_create_order(
    #             symbol=symbol,
    #             side='BUY',
    #             type='MARKET',
    #             quantity=qty,
    #             recvWindow=self.recvWindow
    #         )
    #             return_dict['state'] = 'OK'
    #         except Exception as e:
    #             self.binance_plug_logger.error(f"binance_market_exit|{traceback.format_exc()}")
    #             return_dict['res'] = e
    #             return_dict['state'] = 'ERROR'

    def okx_market_exit(self, user_okx_access_key, user_okx_secret_key, passphrase, symbol, qty, mgnMode, return_dict=None):
        if qty < 0:
            converted_qty = -qty
            okx_client = self.load_user_client(user_okx_access_key, user_okx_secret_key, passphrase)
            # retry_count = 0

            # while retry_count <= self.retry_count_limit:
            #     if retry_count >= 1:
            #         self.binance_plug_logger.info(f"binance_market_exit|retry_count: {retry_count}, retry_term_sec: {self.retry_term_sec}, retry_count_limit: {self.retry_count_limit}") # For TESTING
            #     try:
            #         res = bi_client.futures_create_order(
            #         symbol=symbol,
            #         side='BUY',
            #         type='MARKET',
            #         quantity=qty,
            #         recvWindow=self.recvWindow
            #         )
            #         if return_dict is not None:
            #             return_dict['res'] = res
            #             return_dict['state'] = 'OK'
            #         return res
            #     except Exception as e:
            #         if e.code not in [-1000, -1001] or retry_count == self.retry_count_limit:
            #             if return_dict is None:
            #                 raise e
            #             else:
            #                 return_dict['res'] = e
            #                 return_dict['state'] = 'ERROR'
            #                 return
            #     retry_count += 1
            try:
                res = okx_client.TradeAPI.place_order(symbol, mgnMode, 'buy', 'market', self.convert_qty_to_sz(symbol, converted_qty))['data'][0]
            except Exception as e:
                res = {}
                res['sCode'] = "-1"
                res['sMsg'] = traceback.format_exc()
                self.okx_plug_logger.error(f"okx_market_exit|{symbol}|{qty}|{traceback.format_exc()}")
            if return_dict is not None:
                return_dict['res'] = res
                if res['sCode'] == '0':
                    return_dict['state'] = 'OK'
                else:
                    return_dict['state'] = 'ERROR'
            return res
        else:
            res = {"sMsg": f"현재 LONG 포지션만 보유하고 있으므로 정리할 수 없습니다. 포지션 정보: {symbol} LONG {qty}개", "sCode": "-1"}
            if return_dict is not None:
                return_dict['res'] = res
                return_dict['state'] = 'ERROR'
            return res
        

    def okx_position_information(self, user_okx_access_key, user_okx_secret_key, passphrase, symbol=None, return_dict=None):
        okx_client = self.load_user_client(user_okx_access_key, user_okx_secret_key, passphrase)
        error_switch = False
        try:
            raw_res = okx_client.AccountAPI.get_positions()
            position_df = pd.DataFrame(raw_res['data'])
            if len(position_df) == 0:
                position_df = pd.DataFrame(columns=['adl', 'availPos', 'avgPx', 'baseBal', 'baseBorrowed', 'baseInterest',
            'bizRefId', 'bizRefType', 'cTime', 'ccy', 'closeOrderAlgo', 'deltaBS',
            'deltaPA', 'gammaBS', 'gammaPA', 'idxPx', 'imr', 'instId', 'instType',
            'interest', 'last', 'lever', 'liab', 'liabCcy', 'liqPx', 'margin',
            'markPx', 'mgnMode', 'mgnRatio', 'mmr', 'notionalUsd', 'optVal',
            'pendingCloseOrdLiabVal', 'pos', 'posCcy', 'posId', 'posSide',
            'quoteBal', 'quoteBorrowed', 'quoteInterest', 'spotInUseAmt',
            'spotInUseCcy', 'thetaBS', 'thetaPA', 'tradeId', 'uTime', 'upl',
            'uplLastPx', 'uplRatio', 'uplRatioLastPx', 'usdPx', 'vegaBS', 'vegaPA', 'qty'])
            if symbol is not None:
                position_df = position_df[position_df['instId']==symbol]
            position_df.loc[:, 'pos'] = position_df['pos'].astype(float)
            merged_position_df = position_df.merge(self.instrument_info[['instId','ctVal']], left_on='instId', right_on='instId')
            merged_position_df.loc[:, 'ctVal'] = merged_position_df['ctVal'].astype(float)
            merged_position_df['qty'] = merged_position_df['pos'] * merged_position_df['ctVal']
            aggregated_df = merged_position_df.groupby('instId').sum().reset_index()[['instId','upl','qty']]
            aggregated_df['mgnMode'] = 'total'
            merged_position_df = pd.concat([merged_position_df, aggregated_df], axis=0)
            final_merged_position_df = merged_position_df[['instId','upl','lever','qty','liqPx','posSide','mgnMode']].set_index('mgnMode')#.to_dict('index')
            if len(final_merged_position_df) != 0:
                merged_position_series = final_merged_position_df.groupby('mgnMode').apply(lambda x: x.to_dict('records'))
            else:
                merged_position_series = pd.Series()
            for each_mgnMode in ['cross', 'isolated', 'total']:
                if each_mgnMode not in merged_position_series.index:
                    merged_position_series.loc[each_mgnMode] = [{'instId': symbol, 'qty': 0, 'upl': 0, 'lever': None, 'liqPx': '', 'posSide': None}]
            merged_position_dict = merged_position_series.to_dict()
            for each_list in merged_position_dict.values():
                for each_dict in each_list:
                    if each_dict['liqPx'] == '':
                        each_dict['liqPx'] = None
                    else:
                        each_dict['liqPx'] = float(each_dict['liqPx'])
        except Exception as e:
            error_switch = True
            merged_position_dict = {"sMsg": traceback.format_exc()}
            self.okx_plug_logger.error(f"okx_position_information|{traceback.format_exc()}")
        if return_dict is not None:
            if error_switch is False:
                return_dict['state'] = 'OK'
            else:
                return_dict['state'] = 'ERROR'
            return_dict['res'] = merged_position_dict
        return merged_position_dict

    # def binance_get_futures_account(self, user_binance_access_key, user_binance_secret_key, return_dict=None):
    #     bi_client = self.load_user_client(user_binance_access_key, user_binance_secret_key)
    #     if return_dict is None:
    #         res = bi_client.futures_account()
    #         res_df = pd.DataFrame(res['assets'])
    #         res_df.loc[:, 'walletBalance':'updateTime'] = res_df.loc[:, 'walletBalance':'updateTime'].astype(float)
    #         return res_df
    #     else:
    #         try:
    #             res = bi_client.futures_account()
    #             res_df = pd.DataFrame(res['assets'])
    #             res_df.loc[:, 'walletBalance':'updateTime'] = res_df.loc[:, 'walletBalance':'updateTime'].astype(float)
    #             return_dict['res'] = res_df
    #             return_dict['state'] = 'OK'
    #         except Exception as e:
    #             self.binance_plug_logger.error(f"binance_get_futures_account|{traceback.format_exc()}")
    #             return_dict['res'] = e
    #             return_dict['state'] = 'ERROR'

    # def binance_usdm_fundingrate(self):
    #     bi_client = self.pub_bi_client
    #     binance_fund = pd.DataFrame(bi_client.futures_mark_price())[['symbol','lastFundingRate','nextFundingTime']]
    #     binance_fund = binance_fund.rename(columns={'symbol':'binance', 'lastFundingRate':'binance_fundingrate', 'nextFundingTime':'fundingtime'})
    #     binance_fund.iloc[:,-1] = binance_fund.iloc[:,-1].apply(lambda x: datetime.datetime.fromtimestamp(x/1000))
    #     binance_fund['symbol'] = binance_fund['binance'].apply(lambda x: x.replace('USDT',''))
    #     first_column = binance_fund.pop('symbol')
    #     binance_fund.insert(0, 'symbol', first_column)
    #     binance_fund = binance_fund[~binance_fund['binance'].str.contains(r'\d')].reset_index(drop=True)
    #     binance_fund = binance_fund.rename(columns={'binance':'full_symbol', 'binance_fundingrate':'fundingrate'})
    #     binance_fund['last_updated_time'] = datetime.datetime.now()
    #     binance_fund['exchange'] = 'binance'
    #     return binance_fund

    # def binance_get_futures_exchange_info(self):
    #     bi_client = self.pub_bi_client
    #     futures_exchange_info_df = pd.DataFrame(bi_client.futures_exchange_info()['symbols'])
    #     futures_exchange_info_df.loc[:, 'filters'] = futures_exchange_info_df['filters'].apply(lambda x: x[2]['maxQty'])
    #     futures_exchange_info_df = futures_exchange_info_df.rename(columns={'filters':'MarketOrder_maxQty'})
    #     return futures_exchange_info_df

    # 여기서부터
    # OKX Fetching candles
    def okx_fetch_candle(self, symbol, period, count=200):
        if type(period) == int:
            if period < 60:
                period = f'{period}m'
            else:
                period = f'{int(period/60)}H'
        elif period == 'days':
            period = '1D'

        elif period == 'weeks':
            period = '1W'

        else:
            print('Error occured while processing period.')

        kline = self.pub_okx_client.MarketAPI.get_candlesticks(instId=symbol, bar=period, limit=str(count))
        kline = pd.DataFrame(kline['data'])
        kline.loc[:, 0] = kline.loc[:, 0].apply(lambda x: datetime.datetime.fromtimestamp(float(x)/1000))
        columns = ['okx_time', 'okx_open', 'okx_high', 'okx_low', 'okx_close', 'okx_volume', 'okx_volCcy','okx_volCcyQuote','okx_completed']
        kline.columns = columns
        kline.loc[:, [x for x in columns if x != 'okx_time']] = kline.loc[:, [x for x in columns if x != 'okx_time']].astype(float)
        return kline
