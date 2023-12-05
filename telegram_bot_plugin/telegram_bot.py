import datetime
from distutils.cmd import Command
import re
import time
import os
import sys
import traceback
import telegram
import pandas as pd
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler, CallbackContext
from threading import Thread

upper_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(upper_dir)
from loggers.logger import KimpBotLogger
from etc.redis_connector.redis_connector import InitRedis

####################################################################################################################################

class MyTelegramBot(telegram.Bot):
    def __init__(self, logger, token, request):
        self.my_logger = logger
        self.my_logger.info("MyTelegramBot Logger started.")
        super().__init__(token=token, request=request)

    def send_thread(self, chat_id, text, alarm_num=1, alarm_period=1, parse_mode=None, reply_markup=None):
        if parse_mode == 'html':
            parse_mode = telegram.ParseMode.HTML

        
        # if len(text) >= 1995:
        #     text = text[:1995]
        def th():
            try:
                for _ in range(alarm_num):
                    input_text = text
                    cut_unit = 1995
                    if len(input_text) <= cut_unit:
                        # print(input_text)
                        self.send_message(chat_id=int(chat_id), text=input_text, parse_mode=parse_mode, reply_markup=reply_markup)
                    else:
                        while len(input_text) > cut_unit:
                            line_change_iter = re.finditer('\n', input_text)
                            line_change_index_list = [x.span()[0] for x in line_change_iter if x.span()[0] <= cut_unit]
                            if line_change_index_list == []:
                                # print(input_text[:cut_unit])
                                self.send_message(chat_id=int(chat_id), text=input_text[:cut_unit], parse_mode=parse_mode, reply_markup=reply_markup)
                            else:
                                last_index = line_change_index_list[-1]
                                body = input_text[:last_index]
                                # print(body)
                                self.send_message(chat_id=int(chat_id), text=body, parse_mode=parse_mode, reply_markup=reply_markup)
                                input_text = input_text[last_index+1:]
                            # print(f"\nlen(input_text): {len(input_text)}\n")
                            if len(input_text) <= cut_unit:
                                # print(input_text)
                                self.send_message(chat_id=int(chat_id), text=input_text, parse_mode=parse_mode, reply_markup=reply_markup)

                    # self.send_message(chat_id=int(chat_id), text=text, parse_mode=parse_mode, reply_markup=reply_markup)
                    if alarm_num > 1:
                        time.sleep(alarm_period)
                return
            except Exception:
                self.my_logger.error(f"alarm_thread|user_id:{chat_id}, body:{text}")
                self.my_logger.error(f"{traceback.format_exc()}")
        alarm_t = Thread(target=th, daemon=True)
        alarm_t.start()

    def send_thread_split_by_number(self, user_id, body, alarm_num=1, alarm_period=1, parse_mode=telegram.ParseMode.HTML, reply_markup=None):
        # send message
        try:
            if len(body) <= 1995:
                self.send_thread(user_id, body, alarm_num, alarm_period, parse_mode, reply_markup)
                return
            else:
                start_indices = [x.start() for x in re.finditer('<b>[0-9]+.', body)]
                for i in range((len(body)//1995)+1):
                    i += 1
                    if i == 1:
                        start_index = 0
                    end_index = max([x for x in start_indices if x < 1995*i])
                    if i != ((len(body)//1995)+1):
                        self.send_thread(user_id, body[start_index:end_index], alarm_num, alarm_period, parse_mode)
                    else:
                        self.send_thread(user_id, body[start_index:], alarm_num, alarm_period, parse_mode, reply_markup)
                    start_index = end_index
                return
        except Exception:
            self.my_logger.error(f"send_message_split_by_number|user_id: {user_id}, body: {body}")
            self.my_logger.error(f"{traceback.format_exc()}")

####################################################################################################################################

class InitTelegramBot:
    def __init__(self, bot_token, logging_dir, node, db_dict, core, register_monitor_msg, admin_id_list, total_enabled_market_klines):
        self.node = node
        # self.encryption_key = encryption_key
        self.core = core
        self.check_status = core.check_status
        self.dollar_update_thread_status = core.dollar_update_thread_status
        self.reinitiate_dollar_update_thread = core.reinitiate_dollar_update_thread
        self.get_dollar_dict = core.get_dollar_dict
        self.admin_id_list = admin_id_list
        self.telegram_bot_logger = KimpBotLogger("telegram_bot_logger", logging_dir).logger
        self.updater = Updater(token=bot_token, request_kwargs={'read_timeout': 30, 'connect_timeout': 30})
        self.dispatcher = self.updater.dispatcher
        self.total_enabled_market_klines = total_enabled_market_klines
        self.total_enabled_markets = []
        self._get_total_enabled_markets()
        request_object = telegram.utils.request.Request(connect_timeout=30.0, read_timeout=30.0)
        # self.bot = telegram.Bot(token=bot_token, request=request_object)
        self.bot = MyTelegramBot(logger=self.telegram_bot_logger, token=bot_token, request=request_object)
        self.redis_client_db0 = InitRedis()
        # self.db_dict = db_dict

        # dispatching handlers
        start_handler = CommandHandler('start', self.start)
        self.dispatcher.add_handler(start_handler)
        help_handler = CommandHandler('help', self.help)
        self.dispatcher.add_handler(help_handler)
        server_check_handler = CommandHandler('server_check', self.server_check)
        self.dispatcher.add_handler(server_check_handler)
        cancel_server_check_handler = CommandHandler('cancel_server_check', self.cancel_server_check)
        self.dispatcher.add_handler(cancel_server_check_handler)

        ##### Functions for management############################
        rec_message_handler = CommandHandler('rec', self.rec)
        self.dispatcher.add_handler(rec_message_handler)
        admin_msgto_handler = CommandHandler('msgto', self.msgto)
        self.dispatcher.add_handler(admin_msgto_handler)
        status_handler = CommandHandler('status', self.status)
        self.dispatcher.add_handler(status_handler)
        check_symbols_handler = CommandHandler('check_symbols', self.check_symbols)
        self.dispatcher.add_handler(check_symbols_handler)
        ##### Functions for system management############################
        stop_handler = CommandHandler('stop', self.stop)
        self.dispatcher.add_handler(stop_handler)
        restart_handler = CommandHandler('restart', self.restart)
        self.dispatcher.add_handler(restart_handler)
        redollar_handler = CommandHandler('redollar', self.redollar)
        self.dispatcher.add_handler(redollar_handler)
        ###### Functions for testing ##################################
        add_to_exclude_handler = CommandHandler('add_to_exclude', self.add_to_exclude)
        self.dispatcher.add_handler(add_to_exclude_handler)
        remove_to_exclude_handler = CommandHandler('remove_to_exclude', self.remove_to_exclude)
        self.dispatcher.add_handler(remove_to_exclude_handler)
        ########### Normal message handler ##############################
        # process_message_handler = MessageHandler(Filters.text & ~Filters.command, self.process_message)
        # self.dispatcher.add_handler(process_message_handler)
        ########### Unknown handler ##############################
        unknown_handler = MessageHandler(Filters.command, self.unknown)
        self.dispatcher.add_handler(unknown_handler)

        # start polling
        self.updater.start_polling()

    def _get_total_enabled_markets(self):
        for each_market_combi_code in self.total_enabled_market_klines:
            target_market_code, origin_market_code = each_market_combi_code.split(':')
            target_market = target_market_code.split('/')[0]
            origin_market = origin_market_code.split('/')[0]
            self.total_enabled_markets.append(target_market)
            self.total_enabled_markets.append(origin_market)
        self.total_enabled_markets = list(set(self.total_enabled_markets))

######### telegram chat functions####################################################################################################

    def start(self, update, context):
        def start_thread():
            if update.effective_chat.id not in self.admin_id_list:
                return
            body = f"info_core 관리용 봇 입니다.."
            self.bot.send_thread(update.effective_chat.id, body, parse_mode='html')
        start_thread_th = Thread(target=start_thread, daemon=True)
        start_thread_th.start()

    def help(self, update, context):
        def help_thread():
            body = f"info_core 관리용 봇 입니다.."
            body += f"\n/status"
            body += f"\n/server_check"
            body += f"\n/cancel_server_check"
            self.bot.send_thread(update.effective_chat.id, body, parse_mode='html')
        help_thread_th = Thread(target=help_thread, daemon=True)
        help_thread_th.start()

    def server_check(self, update, context):
        def server_check_thread():
            user_id = update.effective_chat.id
            if user_id in self.admin_id_list:
                try:
                    if context.args == []:
                        body = f"서버 점검 등록 명령어 입니다."
                        body += f"\n/server_check 마켓이름, 시작시간, 종료시간 순으로 입력해주세요. 시간은 UTC 기준입니다."
                        body += f"\nex)/server_check BINANCE_USD_M, 2023-12-01T00:00, 2023-12-01T09:00"
                        body += f"\n마켓 목록: {self.total_enabled_markets}"
                        self.bot.send_thread(chat_id=user_id, text=body)
                        return
                    input_msg = ''.join(context.args).split(',')
                    if len(input_msg) != 3:
                        body = f"잘못된 입력입니다.\n"
                        body += f"/server_check 마켓이름, 시작시간, 종료시간 순으로 입력해주세요. 시간은 UTC 기준입니다."
                        body += f"\nex)/server_check BINANCE_USD_M, 2023-12-01T00:00, 2023-12-01T09:00"
                        body += f"\n마켓 목록: {self.total_enabled_markets}"
                        self.bot.send_thread(chat_id=user_id, text=body)
                        return
                    if input_msg[0].upper() not in self.total_enabled_markets:
                        body = f"잘못된 입력입니다.\n"
                        body += f"지원하지 않는 마켓 입니다. 지원되는 마켓목록은 {self.total_enabled_markets} 입니다."
                        self.bot.send_thread(chat_id=user_id, text=body)
                        return
                    market = input_msg[0].upper()
                    utc_now_timestamp = datetime.datetime.utcnow().timestamp()
                    start_utc_timestamp = datetime.datetime.strptime(input_msg[1], '%Y-%m-%dT%H:%M').timestamp()
                    end_utc_timestamp = datetime.datetime.strptime(input_msg[2], '%Y-%m-%dT%H:%M').timestamp()
                    if start_utc_timestamp < utc_now_timestamp:
                        body = f"시작시간이 현재시간보다 이전입니다."
                        self.bot.send_thread(chat_id=user_id, text=body)
                        return
                    if end_utc_timestamp < start_utc_timestamp:
                        body = f"종료시간이 시작시간보다 이전입니다."
                        self.bot.send_thread(chat_id=user_id, text=body)
                        return
                    # Passed validation
                    # Register in Redis db
                    self.redis_client_db0.set_dict(f"INFO_CORE|SERVER_CHECK|{market}", {"start": start_utc_timestamp, "end": end_utc_timestamp}, ex=int(end_utc_timestamp-utc_now_timestamp+5))
                    body = f"예약된 {market} 마켓의 서버점검 시작시간은"
                    body += f"\nKST:{datetime.datetime.fromtimestamp(start_utc_timestamp)+datetime.timedelta(hours=9)}~{datetime.datetime.fromtimestamp(end_utc_timestamp)+datetime.timedelta(hours=9)}이며,"
                    body += f"\nUTC:{datetime.datetime.fromtimestamp(start_utc_timestamp)}~{datetime.datetime.fromtimestamp(end_utc_timestamp)}입니다."
                    body += f"\n현재시간은 KST:{datetime.datetime.fromtimestamp(utc_now_timestamp)+datetime.timedelta(hours=9)}, UTC:{datetime.datetime.fromtimestamp(utc_now_timestamp)}이므로,"
                    body += f"\n서버점검 시작시간까지 {int((start_utc_timestamp-utc_now_timestamp)/3600)}시간 {int(((start_utc_timestamp-utc_now_timestamp)%3600)/60)}분,"
                    body += f"\n서버점검 종료시간까지 {int((end_utc_timestamp-utc_now_timestamp)/3600)}시간 {int(((end_utc_timestamp-utc_now_timestamp)%3600)/60)}분 남았습니다."
                    self.bot.send_thread(chat_id=user_id, text=body)
                    return
                except Exception as e:
                    self.telegram_bot_logger.error(f"server_check|{traceback.format_exc()}")
                    body = f"서비스에 불편을 드려 죄송합니다. 일시적인 오류가 발생했습니다. 관리자에게 문의 해 주세요. (@charlie1155)\n"
                    body += f"error: {e}"
                    self.bot.send_thread(chat_id=user_id, text=body)
                    return
        server_check_thread_th = Thread(target=server_check_thread, daemon=True)
        server_check_thread_th.start()
    
    def cancel_server_check(self, update, context):
        def cancel_server_check_thread():
            user_id = update.effective_chat.id
            if user_id in self.admin_id_list:
                try:
                    registered_server_check_list = [x.decode('utf-8') for x in self.redis_client_db0.redis_conn.keys() if 'INFO_CORE|SERVER_CHECK' in x.decode('utf-8')]
                    if context.args == []:
                        body = f"서버 점검 등록 취소 명령어 입니다."
                        body += f"\n/server_check 마켓이름 으로 입력해주세요."
                        body += f"\nex)/server_check BINANCE_USD_M"
                        body += f"\nRedis 에 등록된 서버 점검 목록: {registered_server_check_list}"
                        self.bot.send_thread(chat_id=user_id, text=body)
                        return
                    input_msg = ''.join(context.args).split(',')
                    if len(input_msg) != 1:
                        body = f"잘못된 입력입니다.\n"
                        body += f"/server_check 마켓이름 형식으로 입력해주세요."
                        body += f"\nex)/server_check BINANCE_USD_M"
                        body += f"\nRedis 에 등록된 서버 점검 목록: {registered_server_check_list}"
                        self.bot.send_thread(chat_id=user_id, text=body)
                        return
                    # Passed validation
                    market = input_msg[0].upper()
                    selected_server_check_list = [x for x in registered_server_check_list if market in x]
                    if selected_server_check_list == []:
                        body = f"{market}에 대한 서버점검 예약이 없습니다."
                        self.bot.send_thread(chat_id=user_id, text=body)
                        return
                    else:
                        for each_server_check in selected_server_check_list:
                            self.redis_client_db0.redis_conn.delete(each_server_check)
                            body = f"{market}에 대한 서버점검 예약({each_server_check})이 취소되었습니다."
                            self.bot.send_thread(chat_id=user_id, text=body)
                        return
                except Exception as e:
                    self.telegram_bot_logger.error(f"cancel_server_check_thread_th|{traceback.format_exc()}")
                    body = f"서비스에 불편을 드려 죄송합니다. 일시적인 오류가 발생했습니다. 관리자에게 문의 해 주세요. (@charlie1155)\n"
                    body += f"error: {e}"
                    self.bot.send_thread(chat_id=user_id, text=body)
                    return
        cancel_server_check_thread_th = Thread(target=cancel_server_check_thread, daemon=True)
        cancel_server_check_thread_th.start()


############# Functions for management ###########################################################################
    def rec(self, update, context):
        user_id = update.effective_chat.id
        for admin_id in self.admin_id_list:
            self.bot.send_thread(chat_id=admin_id, text=str(user_id))
            self.bot.send_thread(chat_id=user_id, text=f'식별 ID가 관리자에게 전송되었습니다. 잠시만 기다려 주세요.')
    
    def msgto(self, update, context):
        def send_thread():
            user_id = update.effective_chat.id
            if user_id in self.admin_id_list:
                try:
                    if context.args == []:
                        body = f"/msgto user_id message 형식으로 입력하세요."
                        self.bot.send_thread(chat_id=user_id, text=body)
                        return
                    input_msg = context.args
                    if len(input_msg) < 2:
                        body = f"잘못된 입력입니다.\n"
                        body += f"/send user_id message 형식으로 입력하세요."
                        self.bot.send_thread(chat_id=user_id, text=body)
                        return
                    # db_client = InitDBClient(**self.local_db_dict)
                    # db_client.curr.execute("""SELECT user_id FROM user_info""")
                    # db_client.conn.close()
                    # output = db_client.curr.fetchall()
                    # user_id_list = pd.DataFrame(output)['user_id'].tolist()
                    input_user_id = int(input_msg[0].replace(',',''))
                    # if input_user_id not in user_id_list:
                    #     body = f"user_id: {input_user_id}는 Database에 등록된 유저가 아닙니다."
                    #     self.bot.send_thread(chat_id=self.admin_id, text=body)
                    #     return
                    # Passed validation
                    self.bot.send_thread(chat_id=input_user_id, text=' '.join(input_msg[1:]))
                    return
                except Exception as e:
                    self.telegram_bot_logger.error(f"msgto|{traceback.format_exc()}")
                    body = f"서비스에 불편을 드려 죄송합니다. 일시적인 오류가 발생했습니다. 관리자에게 문의 해 주세요. (@charlie1155)\n"
                    body += f"error: {e}"
                    self.bot.send_thread(chat_id=user_id, text=body)
                    return
        admin_message_thread_th = Thread(target=send_thread, daemon=True)
        admin_message_thread_th.start()

    def status(self, update, context):
        def status_thread():
            user_id = update.effective_chat.id
            if user_id in self.admin_id_list:
                try:
                    websocket_integrity_flag, whole_status_str = self.check_status(include_text=True)
                    dollar_update_integrity_flag, dollar_update_status_str = self.dollar_update_thread_status()
                    body = whole_status_str + '\n'
                    body += f"\nDollar Update Thread Status"
                    body += f'\n{dollar_update_status_str}'
                
                    self.bot.send_thread(chat_id=user_id, text=body)
                except Exception as e:
                    self.telegram_bot_logger.error(f"status|{traceback.format_exc()}")
                    body = f"서비스에 불편을 드려 죄송합니다. 일시적인 오류가 발생했습니다. 관리자에게 문의 해 주세요. (@charlie1155)\n"
                    body += f"error: {e}"
                    self.bot.send_thread(chat_id=user_id, text=body)
                    return
        status_thread_th = Thread(target=status_thread, daemon=True)
        status_thread_th.start()
    
    def check_symbols(self, update, context):
        def check_symbols_thread():
            user_id = update.effective_chat.id
            if user_id in self.admin_id_list:
                try:
                    # read input message
                    input_msg = context.args
                    exchange_name = input_msg[0].upper()
                    if exchange_name not in ['UPBIT_SPOT', 'BINANCE_USD_M']:
                        body = f"exchange_name: {exchange_name}은 지원하지 않는 거래소 입니다."
                        self.bot.send_thread(chat_id=user_id, text=body)
                        return
                    # Passed validation
                    content = ""
                    for proc_name, symbol_list in self.core.exchange_websocket_dict[exchange_name].websocket_symbol_dict.items():
                        content += f"{proc_name}\n"
                        for symbol in symbol_list:
                            content += f"{symbol}\n"
                        content += "\n"
                    self.bot.send_thread(chat_id=user_id, text=content)

                except Exception as e:
                    self.telegram_bot_logger.error(f"check_symbols|{traceback.format_exc()}")
                    body = f"서비스에 불편을 드려 죄송합니다. 일시적인 오류가 발생했습니다. 관리자에게 문의 해 주세요. (@charlie1155)\n"
                    body += f"error: {e}"
                    self.bot.send_thread(chat_id=user_id, text=body)
                    return
        check_symbols_thread_th = Thread(target=check_symbols_thread, daemon=True)
        check_symbols_thread_th.start()

    # System handling functions
    ######################################################################################
    def stop(self, update, context):
        user_id = update.effective_chat.id
        if user_id not in self.admin_id_list:
            return
        try:
            # pm2_name = 'kp_trade_v2'
            # self.bot.send_thread(chat_id=user_id, text=f"Stopping kimp bot... sending pm2 stop {pm2_name}")
            # result = os.system(f"pm2 stop {pm2_name}")
            # self.bot.send_thread(chat_id=user_id, text=result)
            pass
        except Exception as e:
            body = f"서비스에 불편을 드려 죄송합니다. 일시적인 오류가 발생했습니다. 관리자에게 문의 해 주세요. (@charlie1155)\n"
            body += f"error: {e}"
            self.bot.send_thread(chat_id=user_id, text=body)
            return
        
    def restart(self, update, context):
        user_id  =update.effective_chat.id
        if user_id not in self.admin_id_list: # 나, 영익이형, 준우형, 홍갑이형
            return
        try:
            # systemd_name = 'kp_trade_v2'
            # self.bot.send_message(chat_id=user_id, text=f"Restarting kimp bot... for {systemd_name}")
            # restart_dir = os.getcwd() + '/restart.sh'
            # os.system(restart_dir)
            # self.bot.send_thread(chat_id=self.admin_id, text='After restart_proc executed.')
            pass
        except Exception as e:
            body = f"서비스에 불편을 드려 죄송합니다. 일시적인 오류가 발생했습니다. 관리자에게 문의 해 주세요. (@charlie1155)\n"
            body += f"error: {e}"
            self.bot.send_thread(chat_id=user_id, text=body)
            return
        
    def redollar(self, update, context):
        user_id = update.effective_chat.id
        if user_id not in self.admin_id_list: # 나, 영익이형, 준우형, 홍갑이형
            return
        try:
            # systemd_name = 'kp_trade_v2'
            # self.bot.send_message(chat_id=user_id, text=f"Reinitiating dollar_update_thread... for {systemd_name}")
            # reinitiating_dollar_thread_res = self.reinitiate_dollar_update_thread()
            # self.bot.send_thread(chat_id=self.admin_id, text=reinitiating_dollar_thread_res)
            pass
        except Exception as e:
            body = f"서비스에 불편을 드려 죄송합니다. 일시적인 오류가 발생했습니다. 관리자에게 문의 해 주세요. (@charlie1155)\n"
            body += f"error: {e}"
            self.bot.send_thread(chat_id=user_id, text=body)
            return
        
    # Testing functions #######################################################################################################
    def add_to_exclude(self, update, context):
        user_id = update.effective_chat.id
        if user_id not in self.admin_id_list: # 나, 영익이형, 준우형, 홍갑이형
            return
        try:
            input_msg = ''.join(context.args).split(',')
            if len(input_msg) != 2:
                body = f"잘못된 입력입니다. self.binance_usdm_symbols_to_exclude: {self.core.binance_usdm_symbols_to_exclude}\n"
                body += f"/add_to_exclude market_code, base_asset 형식으로 입력하세요. ex) BINANCE_USD_M, BTC"
                self.bot.send_thread(chat_id=user_id, text=body)
                return
            if input_msg[0].upper() not in ['BINANCE_USD_M', 'BINANCE_SPOT', 'BINANCE_COIN_M', 'UPBIT_SPOT']:
                body = f"잘못된 입력입니다.\n"
                body += f"지원하지 않는 마켓 입니다. 지원되는 마켓은 BINANCE_USD_M, BINANCE_SPOT, BINANCE_COIN_M, UPBIT_SPOT 입니다."
                self.bot.send_thread(chat_id=user_id, text=body)
                return
            # Passed validation
            market_code = input_msg[0].upper()
            base_asset = input_msg[1].upper()
            self.core.add_symbol_to_exclude(market_code, base_asset)
        except Exception as e:
            body = f"서비스에 불편을 드려 죄송합니다. 일시적인 오류가 발생했습니다. 관리자에게 문의 해 주세요. (@charlie1155)\n"
            body += f"error: {e}"
            self.bot.send_thread(chat_id=user_id, text=body)
            return
    
    def remove_to_exclude(self, update, context):
        user_id = update.effective_chat.id
        if user_id not in self.admin_id_list: # 나, 영익이형, 준우형, 홍갑이형
            return
        try:
            input_msg = ''.join(context.args).split(',')
            if len(input_msg) != 2:
                body = f"잘못된 입력입니다.\n"
                body += f"/remove_to_exclude market_code, base_asset 형식으로 입력하세요. ex) BINANCE_USD_M, BTC"
                self.bot.send_thread(chat_id=user_id, text=body)
                return
            if input_msg[0].upper() not in ['BINANCE_USD_M', 'BINANCE_SPOT', 'BINANCE_COIN_M', 'UPBIT_SPOT']:
                body = f"잘못된 입력입니다.\n"
                body += f"지원하지 않는 마켓 입니다. 지원되는 마켓은 BINANCE_USD_M, BINANCE_SPOT, BINANCE_COIN_M, UPBIT_SPOT 입니다."
                self.bot.send_thread(chat_id=user_id, text=body)
                return
            # Passed validation
            market_code = input_msg[0].upper()
            base_asset = input_msg[1].upper()
            self.core.remove_symbol_to_exclude(market_code, base_asset)
        except Exception as e:
            body = f"서비스에 불편을 드려 죄송합니다. 일시적인 오류가 발생했습니다. 관리자에게 문의 해 주세요. (@charlie1155)\n"
            body += f"error: {e}"
            self.bot.send_thread(chat_id=user_id, text=body)
            return

    # handling normal messages from user ######################################################################################
    # unknown command handler/ It must be located at the end of functions
    def unknown(self, update, context):
        text = f"없는 명령어 입니다. /help 를 입력하여 명령어를 확인해 주세요."
        self.bot.send_thread(chat_id=update.effective_chat.id, text=text)
    