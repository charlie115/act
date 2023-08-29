import datetime
from distutils.cmd import Command
import uuid
import base64
import smtplib
from email.mime.text import MIMEText
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
from multiprocessing import Process, Manager

upper_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(upper_dir)
from data_process.processor import InitDataProcessor
from etc.db_handler.create_schema_tables import InitDBClient
from loggers.logger import KimpBotLogger
from trigger_engine.snatcher import InitSnatcher
from trigger_engine.snatcher import krw, redis_uuid_to_display_id, display_id_to_redis_uuid
from langchain_plugin.AIchatbot import ChatBot

# Helper functions
def addcoin_InlineKeyboardButton(user_addcoin_df, user_id):
    user_waiting_coin_df = user_addcoin_df[user_addcoin_df['auto_trade_switch']==-1]
    keyboard = []
    cols = 4
 
    for j,row_tup in enumerate(user_waiting_coin_df.iterrows()):
        if j % cols == 0:
            row_list = []
            keyboard.append(row_list)
        row = row_tup[1]
        redis_uuid = row['redis_uuid']
        addcoin_display_id = redis_uuid_to_display_id(user_addcoin_df, redis_uuid)
        row_list.append(InlineKeyboardButton(f"{addcoin_display_id}정리", callback_data=f'exit,{user_id},{addcoin_display_id}'))
    return InlineKeyboardMarkup(keyboard)

def rmcoin_InlineKeyboardButton(user_addcoin_df, user_id):
    user_not_waiting_coin_df = user_addcoin_df[~(user_addcoin_df['auto_trade_switch']==-1)]
    keyboard = []
    cols = 4
 
    for j,row_tup in enumerate(user_not_waiting_coin_df.iterrows()):
        if j % cols == 0:
            row_list = []
            keyboard.append(row_list)
        row = row_tup[1]
        redis_uuid = row['redis_uuid']
        addcoin_display_id = redis_uuid_to_display_id(user_addcoin_df, redis_uuid)
        row_list.append(InlineKeyboardButton(f"{addcoin_display_id}삭제", callback_data=f'rmcoin,{user_id},{addcoin_display_id}'))
    return InlineKeyboardMarkup(keyboard)

def rmcir_InlineKeyboardButton(user_addcir_df, user_id):
    keyboard = []
    cols = 4
 
    for j,row_tup in enumerate(user_addcir_df.iterrows()):
        if j % cols == 0:
            row_list = []
            keyboard.append(row_list)
        row = row_tup[1]
        addcir_redis_uuid = row['redis_uuid']
        addcir_display_id = redis_uuid_to_display_id(user_addcir_df, addcir_redis_uuid)
        row_list.append(InlineKeyboardButton(f"{addcir_display_id}삭제", callback_data=f'rmcir,{user_id},{addcir_display_id}'))
    return InlineKeyboardMarkup(keyboard)

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
    def __init__(self, logging_dir, node, db_dict, kimp_core, kline_fetcher_proc_status, register_monitor_msg, bot_token, kline_schema_name='coin_kimp_kline', admin_id=1390695186):
        self.node = node
        # self.encryption_key = encryption_key
        self.okx_adaptor = kimp_core.okx_adaptor
        self.upbit_adaptor = kimp_core.upbit_adaptor
        self.websocket_proc_status_func = kimp_core.websocket_proc_status_func
        self.dollar_update_thread_status = kimp_core.dollar_update_thread_status
        self.reinitiate_dollar_update_thread = kimp_core.reinitiate_dollar_update_thread
        self.kline_fetcher_proc_status = kline_fetcher_proc_status
        self.get_kimp_df = kimp_core.get_kimp_df
        self.get_wa_kimp_dict = kimp_core.get_wa_kimp_dict
        self.get_dollar_dict = kimp_core.get_dollar_dict
        self.get_both_listed_okx_symbols = kimp_core.get_both_listed_okx_symbols
        self.get_input_symbol_list = lambda: [x.split('-')[0] for x in self.get_both_listed_okx_symbols()] + [x.split('-')[0]+'USDT' for x in self.get_both_listed_okx_symbols()]
        self.kline_schema_name = kline_schema_name
        self.admin_id = admin_id
        self.telegram_bot_logger = KimpBotLogger("telegram_bot_logger", logging_dir).logger
        self.updater = Updater(token=bot_token, request_kwargs={'read_timeout': 30, 'connect_timeout': 30})
        self.dispatcher = self.updater.dispatcher
        request_object = telegram.utils.request.Request(connect_timeout=30.0, read_timeout=30.0)
        # self.bot = telegram.Bot(token=bot_token, request=request_object)
        self.bot = MyTelegramBot(logger=self.telegram_bot_logger, token=bot_token, request=request_object)
        self.free_service_period = 14
        # self.email_smtp_dict = email_smtp_dict
        self.db_dict = db_dict

        # Server check
        self.upbit_server_check = False
        self.okx_server_check = False

        # Initiate data processor
        self.data_processor = InitDataProcessor(logging_dir, db_dict, kline_schema_name=self.kline_schema_name)

        # Initiate Snatcher
        # self.snatcher = InitSnatcher(logging_dir, node, encryption_key, local_db_dict, remote_db_dict, get_kimp_df, get_wa_kimp_dict_func, get_dollar_dict, monitor_bot_token, monitor_bot_url, self.bot, self.kline_schema_name, admin_id)
        self.snatcher = InitSnatcher(logging_dir, node, encryption_key, local_db_dict, remote_db_dict, kimp_core, monitor_bot_token, monitor_bot_url, self.bot, self.kline_schema_name, admin_id)

        # Initiate AI chatbot
        self.chatbot = ChatBot(logging_dir, node)

        # dispatching handlers
        start_handler = CommandHandler('start', self.start)
        self.dispatcher.add_handler(start_handler)
        help_handler = CommandHandler('help', self.help)
        self.dispatcher.add_handler(help_handler)
        help2_handler = CommandHandler('help2', self.help2)
        self.dispatcher.add_handler(help2_handler)
        help3_handler = CommandHandler('help3', self.help3)
        self.dispatcher.add_handler(help3_handler)
        help4_handler = CommandHandler('help4', self.help4)
        self.dispatcher.add_handler(help4_handler)
        admin_help_handler = CommandHandler('admin_help', self.admin_help)
        self.dispatcher.add_handler(admin_help_handler)
        api_key_handler = CommandHandler('api_key', self.api_key)
        self.dispatcher.add_handler(api_key_handler)
        reset_api_key_handler = CommandHandler('reset_api_key', self.reset_api_key)
        self.dispatcher.add_handler(reset_api_key_handler)
        kp_handler = CommandHandler('kp', self.kp)
        self.dispatcher.add_handler(kp_handler)
        ekp_handler = CommandHandler('ekp', self.ekp)
        self.dispatcher.add_handler(ekp_handler)
        xkp_handler = CommandHandler('xkp', self.xkp)
        self.dispatcher.add_handler(xkp_handler)
        bal_handler = CommandHandler('bal', self.bal)
        self.dispatcher.add_handler(bal_handler)
        pos_handler = CommandHandler('pos', self.pos)
        self.dispatcher.add_handler(pos_handler)
        addint_handler = CommandHandler('addint', self.addint)
        self.dispatcher.add_handler(addint_handler)
        rmint_handler = CommandHandler('rmint', self.rmint)
        self.dispatcher.add_handler(rmint_handler)
        addcoin_handler = CommandHandler('addcoin', self.addcoin)
        self.dispatcher.add_handler(addcoin_handler)
        rmcoin_handler = CommandHandler('rmcoin', self.rmcoin)
        self.dispatcher.add_handler(rmcoin_handler)
        button_callback_handler = CallbackQueryHandler(self.button_callback)
        self.dispatcher.add_handler(button_callback_handler)
        showcoin_handler = CommandHandler('showcoin', self.showcoin)
        self.dispatcher.add_handler(showcoin_handler)
        addcir_handler = CommandHandler('addcir', self.addcir)
        self.dispatcher.add_handler(addcir_handler)
        rmcir_handler = CommandHandler('rmcir', self.rmcir)
        self.dispatcher.add_handler(rmcir_handler)
        showcoin_handler = CommandHandler('showcoin', self.showcoin)
        self.dispatcher.add_handler(showcoin_handler)
        showcir_handler = CommandHandler('showcir', self.showcir)
        self.dispatcher.add_handler(showcir_handler)
        alarm_handler = CommandHandler('alarm', self.alarm)
        self.dispatcher.add_handler(alarm_handler)
        lev_handler = CommandHandler('lev', self.lev)
        self.dispatcher.add_handler(lev_handler)
        mar_handler = CommandHandler('mar', self.mar)
        self.dispatcher.add_handler(mar_handler)
        omit_handler = CommandHandler('omit', self.omit)
        self.dispatcher.add_handler(omit_handler)
        safe_handler = CommandHandler('safe', self.safe)
        self.dispatcher.add_handler(safe_handler)
        addcirl_handler = CommandHandler('addcirl', self.addcirl)
        self.dispatcher.add_handler(addcirl_handler)
        addcirn_handler = CommandHandler('addcirn', self.addcirn)
        self.dispatcher.add_handler(addcirn_handler)
        fundt_handler = CommandHandler('fundt', self.fundt)
        self.dispatcher.add_handler(fundt_handler)
        diff_handler = CommandHandler('diff', self.diff)
        self.dispatcher.add_handler(diff_handler)
        pro_handler = CommandHandler('pro', self.pro)
        self.dispatcher.add_handler(pro_handler)
        his_handler = CommandHandler('his', self.his)
        self.dispatcher.add_handler(his_handler)
        hisf_handler = CommandHandler('hisf', self.hisf)
        self.dispatcher.add_handler(hisf_handler)
        cgh_handler = CommandHandler('cgh', self.cgh)
        self.dispatcher.add_handler(cgh_handler)
        plot_handler = CommandHandler('plot', self.plot)
        self.dispatcher.add_handler(plot_handler)
        plotc_handler = CommandHandler('plotc', self.plotc)
        self.dispatcher.add_handler(plotc_handler)
        enter_handler = CommandHandler('enter', self.enter)
        self.dispatcher.add_handler(enter_handler)
        exit_handler = CommandHandler('exit', self.exit)
        self.dispatcher.add_handler(exit_handler)
        exita_handler = CommandHandler('exita', self.exita)
        self.dispatcher.add_handler(exita_handler)
        std_handler = CommandHandler('std', self.std)
        self.dispatcher.add_handler(std_handler)
        info_handler = CommandHandler('info', self.info)
        self.dispatcher.add_handler(info_handler)
        coupon_handler = CommandHandler('coupon', self.coupon)
        self.dispatcher.add_handler(coupon_handler)
        refer_handler = CommandHandler('refer', self.refer)
        self.dispatcher.add_handler(refer_handler)



        ##### Functions for management############################
        ext_handler = CommandHandler('ext', self.ext)
        self.dispatcher.add_handler(ext_handler)
        extall_handler = CommandHandler('extall', self.extall)
        self.dispatcher.add_handler(extall_handler)
        rec_message_handler = CommandHandler('rec', self.rec)
        self.dispatcher.add_handler(rec_message_handler)
        admin_msgall_handler = CommandHandler('msgall', self.msgall)
        self.dispatcher.add_handler(admin_msgall_handler)
        admin_msgto_handler = CommandHandler('msgto', self.msgto)
        self.dispatcher.add_handler(admin_msgto_handler)
        email_handler = CommandHandler('email', self.email)
        self.dispatcher.add_handler(email_handler)
        server_check_handler = CommandHandler('server_check', self.server_check)
        self.dispatcher.add_handler(server_check_handler)
        addexec_handler = CommandHandler('addexec', self.addexec)
        self.dispatcher.add_handler(addexec_handler)
        rmexec_handler = CommandHandler('rmexec', self.rmexec)
        self.dispatcher.add_handler(rmexec_handler)
        status_handler = CommandHandler('status', self.status)
        self.dispatcher.add_handler(status_handler)
        ##### Functions for system management############################
        stop_handler = CommandHandler('stop', self.stop)
        self.dispatcher.add_handler(stop_handler)
        restart_handler = CommandHandler('restart', self.restart)
        self.dispatcher.add_handler(restart_handler)
        redollar_handler = CommandHandler('redollar', self.redollar)
        self.dispatcher.add_handler(redollar_handler)
        ########### Normal message handler ##############################
        process_message_handler = MessageHandler(Filters.text & ~Filters.command, self.process_message)
        self.dispatcher.add_handler(process_message_handler)
        ########### Unknown handler ##############################
        unknown_handler = MessageHandler(Filters.command, self.unknown)
        self.dispatcher.add_handler(unknown_handler)

        # start polling
        self.updater.start_polling()

######### telegram support functions without dispatchers ####################################################################################################
    def authorize(self, user_id, send_msg=True):
        try:
            if len(self.snatcher.userinfo_df) == 0:
                return False
            user_datetime_end = self.snatcher.userinfo_df[self.snatcher.userinfo_df['user_id']==user_id]['datetime_end'].iloc[0]
            ## TEST
            # user_datetime_end = user_datetime_end - datetime.timedelta(days=4000) 
            if user_datetime_end < datetime.datetime.now():
                if send_msg is True:
                    body = f'이용기간이 만료되었습니다.\n'
                    body += f"추천인쿠폰 등록 및 이용 혹은, 이용권 결제는 영업직원에게 문의바랍니다."
                    self.bot.send_thread(chat_id=user_id, text=body)
                return False
            else:
                return True
        except Exception:
            self.telegram_bot_logger.error(f"authorize|{traceback.format_exc()}")
            return False

    def get_log(self, func_name, update, context, input_text=None, remark=None):
        datetime_now = datetime.datetime.now()
        user_id = update.effective_chat.id
        if input_text is None:
            input_text = ''.join(context.args)
        db_client = InitDBClient(**self.local_db_dict)
        db_client.curr.execute("""INSERT INTO user_log(datetime, user_id, func_name, input, remark) VALUES(%s, %s, %s, %s, %s)""", (datetime_now, user_id, func_name, input_text, remark))
        db_client.conn.commit()
        db_client.conn.close()

    def sign_userinfo(self, update, context, exclude_admin=True):
        try:
            # Sync local user_info with the master_user_info to prevent duplicated registration
            remote_db_client = InitDBClient(**self.remote_db_dict)
            master_res = remote_db_client.curr.execute("""SELECT * FROM master_user_info""")
            if master_res == 0:
                master_user_id_list = []
            else:
                master_user_id_list = pd.DataFrame(remote_db_client.curr.fetchall())['user_id'].tolist()
            local_db_client = InitDBClient(**self.local_db_dict)
            local_res = local_db_client.curr.execute("""SELECT * FROM user_info""")
            if local_res == 0:
                local_user_id_list = []
            else:
                local_user_info_df = pd.DataFrame(local_db_client.curr.fetchall()).dropna(subset=['datetime_end'])
                local_user_id_list = local_user_info_df['user_id'].tolist()
            not_registered_id_list = [x for x in local_user_id_list if x not in master_user_id_list]
            for each_id in not_registered_id_list:
                each_user_datetime = local_user_info_df[local_user_info_df['user_id']==each_id]['datetime'].astype(str).values[0]
                each_user_status = local_user_info_df[local_user_info_df['user_id']==each_id]['status'].values[0]
                each_user_id = each_id
                each_user_name = local_user_info_df[local_user_info_df['user_id']==each_id]['user_name'].values[0]
                each_user_remark = local_user_info_df[local_user_info_df['user_id']==each_id]['remark'].values[0]
                val = [each_user_datetime, each_user_status, each_user_id, each_user_name, self.node, each_user_remark]
                remote_db_client.curr.execute("""INSERT INTO master_user_info(datetime, status, user_id, user_name, registered_node, remark) VALUES(%s,%s,%s,%s,%s,%s)""", val)
            remote_db_client.conn.commit()
            # Local user_info -> master_user_info Sync finished

            # Check whether the new user has already been registered in the master_user_info
            status = 'Normal'
            user_id = update.effective_chat.id
            user_name = update.effective_chat.username
            signed_time = datetime.datetime.now()
            end_time = datetime.datetime.now() # + datetime.timedelta(days=self.free_service_period) # free_service_period will be handled by the coupon function
            master_res = remote_db_client.curr.execute("""SELECT * FROM master_user_info""")
            master_user_id_df = pd.DataFrame(remote_db_client.curr.fetchall())
            if master_res == 0:
                master_user_id_list = []
            else:
                master_user_id_list = master_user_id_df['user_id'].tolist()
            # If a new user is admin and exclude_admin == True
            if user_id == self.admin_id and exclude_admin == True:
                # Check in the local user info and add if not exists (Original func)
                # If there's already data in DB, do nothing
                local_db_client.curr.execute("""SELECT user_id FROM user_info WHERE user_id = %s""", user_id)
                fetched = local_db_client.curr.fetchall()
                if len(fetched) != 0:
                    pass
                else:
                    sql = """
                    INSERT INTO user_info
                    (user_id, register_origin, datetime_end, user_name, okx_leverage, okx_cross, okx_margin_call, safe_reverse, alarm_num, alarm_period, on_off)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    val = [
                        user_id,
                        self.node,
                        end_time,
                        user_name,
                        1,
                        False,
                        None,
                        False,
                        1,
                        1,
                        True
                    ]
                    local_db_client.curr.execute(sql, val)
                    local_db_client. conn.commit()
            # If the new user is not an admin or exclude_admin == False
            else:
                if user_id in master_user_id_list:
                    user_datetime = master_user_id_df[master_user_id_df['user_id']==user_id]['datetime'].values[0]
                    user_registered_node = master_user_id_df[master_user_id_df['user_id']==user_id]['registered_node'].values[0]
                    body = f"이미 김프 트레이딩 봇에 등록된 유저입니다.\n"
                    body += f"최초등록일시: {user_datetime}\n등록서버: {user_registered_node}"
                    self.bot.send_thread(user_id, body)
                    return
                else:
                    # If the user hasn't been registered, register the user into the master and local user_info tables
                    # For master_user_info
                    val = [
                        signed_time,
                        status,
                        user_id,
                        user_name,
                        self.node,
                        None
                    ]
                    remote_db_client.curr.execute("""INSERT INTO master_user_info(datetime, status, user_id, user_name, registered_node, remark) VALUES(%s,%s,%s,%s,%s,%s)""", val)
                    remote_db_client.conn.commit()
                    # For local user_info
                    sql = """
                    INSERT INTO user_info
                    (user_id, register_origin, datetime_end, user_name, okx_leverage, okx_cross, okx_margin_call, safe_reverse, alarm_num, alarm_period, on_off)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    val = [
                        user_id,
                        self.node,
                        end_time,
                        user_name,
                        1,
                        False,
                        False,
                        False,
                        1,
                        1,
                        True
                    ]
                    local_db_client.curr.execute(sql, val)
                    local_db_client.conn.commit()
            remote_db_client.conn.close()
            local_db_client.conn.close()
        except Exception as e:
            self.telegram_bot_logger.error(f"sign_userinfo|{traceback.format_exc()}")
            body = f"죄송합니다. 유저 등록 과정에서 에러가 발생했습니다.\n"
            body += f"Error: {e}\n"
            body += f"관리자 @charlie1155 로 문의해 주세요."
            self.bot.send_thread(update.effective_chat.id, body)

            body = f"ERROR occured while signing up user_id:{update.effective_chat.id}\n"
            body += f"ERROR: {e}"
            self.bot.send_thread(self.admin_id, body)

    def show_addcoin_list(self, fetched_addcoin_df, this_okx_funding_df, fund_string):
        if len(fetched_addcoin_df) == 0:
            body = '없음'
            return body
        else:
            body = ''
            for row_tup in fetched_addcoin_df.iterrows():
                index = row_tup[0] + 1
                row = row_tup[1]
                # load circle_id
                addcoin_uuid = row['addcoin_uuid']
                corr_addcir_df = self.snatcher.addcir_df[self.snatcher.addcir_df['addcir_uuid']==addcoin_uuid]
                if len(corr_addcir_df) == 0:
                    addcir_redis_uuid = "없음"
                else:
                    addcir_redis_uuid = corr_addcir_df['redis_uuid'].values[0]
                if 'USDT' in row['symbol']:
                    temp_str = '원'
                    temp_str2 = '(테더환산)'
                else:
                    temp_str = '%'
                    temp_str2 = ''
                if row['auto_trade_switch'] != None:
                    if row['auto_trade_switch'] == 0:
                        temp_str3 = '진입대기중'
                    elif row['auto_trade_switch'] == -1:
                        if row['enter_okx_orderId'] == None:
                            temp_str3 = f"Enter에러"
                        else:
                            okx_leverage_series = self.snatcher.trade_history_df[self.snatcher.trade_history_df['okx_orderId']==row['enter_okx_orderId']]['okx_leverage']
                            if len(okx_leverage_series) == 0:
                                temp_str3 = f",거래기록없음Error"
                            else:
                                temp_str3 = f'탈출대기중, 레버리지: {okx_leverage_series.values[0]}배'
                                try:
                                    funding_rate = this_okx_funding_df[this_okx_funding_df['full_symbol']==(row['symbol'].replace('USDT','')+'USDT')]['fundingrate'].values[0]
                                    temp_str3 += f"\n  이번타임 펀딩률: {round(100*funding_rate,4)}% {fund_string}"
                                except Exception as e:
                                    admin_body = f"addcoin 펀딩률 추가 에러: {e}\n"
                                    admin_body += f"symbol: {row['symbol']}, redis_uuid: {row['redis_uuid']}"
                                    if row['symbol'] != '1INCH':
                                        self.bot.send_thread(chat_id=self.admin_id, text=admin_body)
                    elif row['auto_trade_switch'] == 1:
                        temp_str3 = '탈출완료'
                    elif row['auto_trade_switch'] == 2:
                        temp_str3 = '탈출Error(미탈출)'
                    temp_str4 = f"{krw(round(row['auto_trade_capital']))}원 "
                else:
                    temp_str3 = '꺼짐'
                    temp_str4 = ''
                addcoin_display_id = redis_uuid_to_display_id(fetched_addcoin_df, row['redis_uuid'])
                addcir_display_id = redis_uuid_to_display_id(self.snatcher.addcir_df, addcir_redis_uuid)
                # body += f"<b>{index}. 코인: {row['symbol']}</b>{temp_str2}, <b>거래ID: {addcoin_display_id}</b>, 반복ID: {addcir_display_id}\n"
                body += f"<b>{index}. 코인: {row['symbol']}</b>{temp_str2}, 연결반복ID: {addcir_display_id}\n"
                body += f"  Low: {row['low']}{temp_str}, High: {row['high']}{temp_str}\n"
                body += f"  자동매매: {temp_str4}{temp_str3}"
                if index != len(fetched_addcoin_df):
                    body += '\n\n'
            return body

    def show_addcir_list(self, fetched_addcir_df, fetched_addcoin_df=None):
        if len(fetched_addcir_df) == 0:
            body = f"\n없음"
            return body
        else:
            body = ''
            for row_tup in fetched_addcir_df.iterrows():
                index = row_tup[0]
                row = row_tup[1]
                addcir_redis_uuid = row['redis_uuid']
                # fetch addcoin redis_uuid
                addcir_uuid = row['addcir_uuid']
                corr_addcoin_df = self.snatcher.addcoin_df[self.snatcher.addcoin_df['addcoin_uuid']==addcir_uuid]
                if len(corr_addcoin_df) == 0:
                    redis_uuid = "없음"
                else:
                    redis_uuid = corr_addcoin_df['redis_uuid'].values[0]
                if row['auto_low'] != None:
                    trade_type = 1
                    trade_type_str = 'auto(수동)'
                elif row['pauto_num'] != None:
                    trade_type = 2
                    trade_type_str = 'pauto(자동)'
                else:
                    trade_type = -1
                    trade_type_str = 'Error'

                # cir_trade_switch == 0 -> Off
                # cir_trade_switch == 1 -> On
                if fetched_addcoin_df is None:
                    addcoin_display_id = redis_uuid_to_display_id(self.snatcher.addcoin_df, redis_uuid)
                else:
                    addcoin_display_id = redis_uuid_to_display_id(fetched_addcoin_df, redis_uuid)
                addcir_display_id = redis_uuid_to_display_id(fetched_addcir_df, addcir_redis_uuid)
                if row['cir_trade_switch'] == 0:
                    status_str = f"꺼짐"
                elif row['cir_trade_switch'] == 1:
                    status_str = f"켜짐"
                if trade_type == 1:
                    if 'USDT' in row['symbol']:
                        temp_str = "원"
                    else:
                        temp_str = "%"
                    # body += f"\n<b>{index+1}. 코인: {row['symbol']}</b>, <b>반복ID:{addcir_display_id}</b>, Low: {row['auto_low']}{temp_str}, High: {row['auto_high']}{temp_str}"
                    body += f"\n<b>{index+1}. 코인: {row['symbol']}</b>, Low: {row['auto_low']}{temp_str}, High: {row['auto_high']}{temp_str}"
                    body += f"\n 상태: <b>{status_str}</b>(연결거래ID:{addcoin_display_id}, {trade_type_str}), 완료: {row['cir_trade_num']}회"
                    body += f"\n 최초운용금액: {krw(round(row['cir_trade_capital']))}원, 비고: {row['remark']}"
                elif trade_type == 2:
                    # body += f"\n<b>{index+1}. 코인: {row['symbol']}</b>, <b>반복ID:{addcir_display_id}</b>, Low_High %폭: {row['pauto_num']}%"
                    body += f"\n<b>{index+1}. 코인: {row['symbol']}</b>, Low_High %폭: {row['pauto_num']}%"
                    body += f"\n 상태: <b>{status_str}</b>(연결거래ID:{addcoin_display_id}, {trade_type_str}), 완료: {row['cir_trade_num']}회"
                    body += f"\n 최초운용금액: {krw(round(row['cir_trade_capital']))}원, 비고: {row['remark']}"
                if index != len(fetched_addcir_df):
                    body += '\n'
            return body
    # need to be checked
    def pauto_func(self, user_id, fetched_addcoin_df, input_msg):
        try:
            overwrite = False
            auto_trade_switch = 0
            pauto_switch = True

            # /addcoin xrp,pauto,1,10000
            if len(input_msg) != 4:
                body = f"잘못된 입력입니다. /addcoin 명령어로 사용법을 확인 해 주세요."
                self.bot.send_thread(chat_id=user_id, text=body)
                return False
            try:
                auto_trade_capital = float(input_msg[3])
                percent_gap = float(input_msg[2])
            except:
                body = f"김프폭% 와 투입자산은 숫자만 입력이 가능합니다."
                self.bot.send_thread(chat_id=user_id, text=body)
                return False
            if percent_gap <= 0:
                body = f"김프폭% 는 0 이하가 될 수 없습니다."
                self.bot.send_thread(chat_id=user_id, text=body)
                return False
            input_symbol = input_msg[0].upper()
            # try to check if the input_symbol is an addcoin_display_id
            try:
                input_addcoin_display_id = int(input_symbol)
                input_redis_uuid = display_id_to_redis_uuid(user_id, self.snatcher.addcoin_df, input_addcoin_display_id)
                not_waiting_fetched_addcoin_df = fetched_addcoin_df[fetched_addcoin_df['auto_trade_switch']!=-1]
                if len(not_waiting_fetched_addcoin_df) == 0:
                    body = f"/addcoin 에 진입대기중 혹은 탈출완료인 거래가 존재하지 않습니다."
                    self.bot.send_thread(chat_id=user_id, text=body)
                    return False
                else:
                    not_waiting_redis_uuid_list = not_waiting_fetched_addcoin_df['redis_uuid'].to_list()
                    if input_redis_uuid not in not_waiting_redis_uuid_list:
                        body = f"/addcoin 에 진입대기중 혹은 탈출완료인 거래ID:{input_redis_uuid} 가 조회되지 않습니다."
                        self.bot.send_thread(chat_id=user_id, text=body)
                        return False
                    input_symbol = not_waiting_fetched_addcoin_df[not_waiting_fetched_addcoin_df['redis_uuid']==input_redis_uuid]['symbol'].values[0]
                    overwrite = True
            # just symbol
            except:
                if input_symbol not in self.get_input_symbol_list():
                    body = f"{input_symbol}은 업비트와 OKX USDT 선물시장에 동시상장되지 않은 코인입니다."
                    self.bot.send_thread(chat_id=user_id, text=body)
                    return False
            # use multiprocessing for drawing a plot
            manager = Manager()
            return_dict = manager.dict()
            get_plot_proc = Process(target=self.data_processor.get_pboundary_plot, args=(input_symbol, 1, percent_gap, return_dict), daemon=True)
            get_plot_proc.start()
            get_plot_proc.join()
            buf, lower_bound, upper_bound = return_dict['return']
            if overwrite == True:
                input_symbol = str(input_addcoin_display_id)
            input_msg = [input_symbol, round(float(lower_bound),3), round(float(upper_bound),3)]

            return auto_trade_switch, pauto_switch, auto_trade_capital, buf, input_msg
        except Exception:
            self.bot.send_thread(self.admin_id, "Error occured in pauto_func!")
            self.telegram_bot_logger.error(f"pauto_func|{traceback.format_exc()}")

    def auto_func(self, user_id, input_msg):
        auto_trade_switch = 0
        auto_index = input_msg.index('AUTO')
        try:
            auto_trade_capital = float(input_msg[auto_index+1])
        except:
            body = f"잘못된 입력입니다. /addcoin 명령어로 사용법을 확인 해 주세요."
            self.bot.send_thread(chat_id=user_id, text=body)
            return False
        input_msg = input_msg[:auto_index]

        return auto_trade_switch, auto_trade_capital, input_msg

    def get_max_input_df(self):
        kimp_df = self.get_kimp_df()
        kimp_df['instId'] = kimp_df['symbol'] + '-USDT-SWAP'
        max_input_df = kimp_df.merge(self.okx_adaptor.instrument_info)[['symbol','trade_price','maxQty']]
        max_input_df['max_input_krw'] = max_input_df['trade_price'] * max_input_df['maxQty']
        return max_input_df

    def deactivate_addcoin_addcir(self, user_id, addcoin_redis_uuid, remark):
        db_client = InitDBClient(**self.local_db_dict)
        db_client.curr.execute("""SELECT * FROM addcir""")
        addcir_df = pd.DataFrame(db_client.curr.fetchall())
        if len(addcir_df) == 0:
            return
        addcir_df = addcir_df.where(addcir_df.notnull(), None)
        if addcoin_redis_uuid == 'ALL': # 로직 변경으로 Deprecated 됨
            db_client.curr.execute("""UPDATE addcir SET last_updated_timestamp=%s, cir_trade_switch=%s, remark=%s WHERE user_id=%s""", (datetime.datetime.now().timestamp()*10000000, 0, remark, user_id))
            db_client.conn.commit()
            body = f"등록된 모든 코인의 /addcir 반복거래 설정이 비활성화 되었습니다."
            self.bot.send_thread(chat_id=user_id, text=body)
        else:
            # Fetch uuid for addcoin
            db_client.curr.execute("""SELECT addcoin_uuid FROM addcoin WHERE redis_uuid=%s""", addcoin_redis_uuid)
            addcoin_uuid = db_client.curr.fetchall()[0]['addcoin_uuid']
            if len(addcir_df[(addcir_df['addcir_uuid']==addcoin_uuid)&(addcir_df['cir_trade_switch']==1)]) == 1:
                addcir_redis_uuid = addcir_df[addcir_df['addcir_uuid']==addcoin_uuid]['redis_uuid'].values[0]
                addcir_symbol = addcir_df[addcir_df['addcir_uuid']==addcoin_uuid]['symbol'].values[0]
                db_client.curr.execute("""UPDATE addcir SET last_updated_timestamp=%s, cir_trade_switch=%s, remark=%s WHERE redis_uuid=%s""", (datetime.datetime.now().timestamp()*10000000, 0, remark, addcir_redis_uuid))
                db_client.conn.commit()
                addcir_display_id = redis_uuid_to_display_id(self.snatcher.addcir_df, addcir_redis_uuid)
                body = f"등록된 {addcir_symbol}(반복ID: {addcir_display_id})의 /addcir 반복거래 설정이 비활성화 되었습니다."
                self.bot.send_thread(chat_id=user_id, text=body)
        db_client.conn.close()
        return

    def button_callback(self, update, CallbackContext):
        """Parses the CallbackQuery and updates the message text."""
        query = update.callback_query
        user_id = query.message.chat.id
        input_data = query.data
        # test
        # print(f"input_data: {input_data}")
        class Object(object):
            pass
        update = Object()
        update.effective_chat = Object()
        update.effective_chat.id = user_id
        context = Object()
        context.bot = self.bot

        if 'kp' in input_data:
            self.kp(update, context)
        elif 'addcoin' in input_data:
            self.addcoin(update, context)
        elif 'exit' in input_data:
            input_msg = input_data.split(',')
            addcoin_display_id = input_msg[2]
            context.args = [addcoin_display_id]
            self.exita(update, context)
        elif 'rmcoin' in input_data:
            input_msg = input_data.split(',')
            addcoin_display_id = input_msg[2]
            context.args = [addcoin_display_id]
            self.rmcoin(update, context)
        elif 'rmcir' in input_data:
            input_msg = input_data.split(',')
            addcir_display_id = input_msg[2]
            context.args = [addcir_display_id]
            self.rmcir(update, context)

    # read addcir and execute /addcoin if it's not registered
    def addcir_addcoin_init(self, trade_type, user_id, symbol, addcir_uuid, auto_low, auto_high, pauto_num, fauto_num, auto_trade_capital):
        try:
            # trade_type == 1 -> auto, 2 -> pauto, 3 -> fauto

            # Read user addcir_limit info and avg_kimp
            user_addcir_limit = self.snatcher.userinfo_df[self.snatcher.userinfo_df['user_id']==user_id]['addcir_limit'].values[0]
            merged_df = self.get_kimp_df()
            # weighted_avg_kimp_per = (merged_df['acc_trade_price_24h']/merged_df['acc_trade_price_24h'].sum() * merged_df['tp_kimp']).sum() * 100
            weighted_avg_kimp_per = self.get_wa_kimp_dict()['wa_kimp'] * 100
            if user_addcir_limit == None:
                user_addcir_limit = 999999
            if user_addcir_limit <= weighted_avg_kimp_per:
                register_deactivate = True
                # Set initial cir_trade_num to -1
                db_client = InitDBClient(**self.local_db_dict)

                db_client.curr.execute("""UPDATE addcir SET last_updated_timestamp=%s, cir_trade_num=%s WHERE addcir_uuid=%s""", (datetime.datetime.now().timestamp()*10000000, -1, addcir_uuid))
                db_client.conn.commit()
                db_client.conn.close()
                # send message
                body = f"설정된 addcirl값({user_addcir_limit}%)보다 현재 평균김프값({round(weighted_avg_kimp_per,4)}%)이 더 높으므로,\n"
                body += f"addcir로 인한 addcoin설정이 비활성화 상태(탈출완료로 표시)로 등록됩니다."
                self.bot.send_thread(chat_id=user_id, text=body)
            else:
                register_deactivate = False

            # make simulated update, context objects to use already defined addcoin function
            class Object(object):
                pass
            update = Object()
            update.effective_chat = Object()
            update.effective_chat.id = user_id

            # register fauto trade
            context = Object()
            context.bot = self.bot
            if trade_type == 1:
                context.args = [symbol, ',', str(auto_low), ',', str(auto_high), ',', 'auto', ',', str(auto_trade_capital)]
            elif trade_type == 2:
                context.args = [symbol, ',', 'pauto', ',', str(pauto_num), ',', str(auto_trade_capital)]
            elif trade_type == 3:    
                context.args = [symbol, ',', 'fauto', ',', str(fauto_num), ',', str(auto_trade_capital)]
            else:
                body = f"addcir_addcoin_init 에서 trade_type 에러 발생.\n"
                body += f"trade_type: {trade_type}, 해당하는 if 처리없음."
                self.bot.send_thread(chat_id=self.admin_id, text=body)
                return
            self.addcoin(update, context, addcir_uuid=addcir_uuid, new=True, register_deactivate=register_deactivate)
            return True
        except Exception as e:
            self.telegram_bot_logger.error(f"addcir_addcoin_init|{traceback.format_exc()}")
            body = f"addcir_addcoin_init 에서 에러 발생.\n"
            body += f"Error: {e}"
            self.bot.send_thread(chat_id=self.admin_id, text=body)
            return

    def send_email(self, title, content, mail_to):
        msg = MIMEText(content)
        msg['From'] = self.email_smtp_dict['email_host_user']
        msg['To'] = mail_to
        msg['Subject'] = title
        s = smtplib.SMTP(self.email_smtp_dict['email_host'], int(self.email_smtp_dict['email_port']))
        s.starttls()
        s.login(self.email_smtp_dict['email_host_user'], self.email_smtp_dict['email_host_password'])
        s.sendmail(self.email_smtp_dict['email_host_user'], mail_to, msg.as_string())
        s.close()
        return

######### telegram chat functions####################################################################################################

    def start(self, update, context):
        def start_thread():
            self.sign_userinfo(update, context)
            # body = f"<b>현재 베타테스트 진행 중으로, 승인된 베타테스터만 이용이 가능합니다.</b>\n"      # For Beta test
            body = f"업비트와 OKX USD-M 선물시장을 활용한 김프거래와 관련된 정보 및 자동거래기능을 제공합니다.\n"
            body += f"해당 봇은 비공개 봇으로, /refer 명령어를 이용하여 추천인 쿠폰을 등록 해 주셔야 이용이 가능합니다.\n"
            body += f"쿠폰등록 후 {self.free_service_period}일 간 무료로 이용이 가능합니다.\n"
            body += f"무료이용기간이 지난 후, 결제는 영업직원에게 문의 바랍니다.\n"
            body += f"봇의 사용방법은 /help 명령어를 입력하여 확인해 주세요."
            self.bot.send_thread(update.effective_chat.id, body, parse_mode='html')
        start_thread_th = Thread(target=start_thread, daemon=True)
        start_thread_th.start()

    def help(self, update, context):
        def help_thread():
            self.get_log('help', update, context)
            body = f"1. 서비스 연장을 위한 결제방법은 영업직원에게 문의 해주세요."
            body += f"\n\n2. /refer 명령어를 입력하면 레퍼럴가입 할인적용을 신청하실 수 있습니다."
            body += f"\n자세한 내용은 /refer 를 입력하여 확인하세요."
            body += f"\n\n3. /info 명령어를 입력하면 계정 설정값과 서비스 이용기간을 확인하실 수 있습니다."
            body += f'\n\n4. /kp 를 입력하면 코인의 실시간 김프를 확인하실 수 있습니다.'
            body += f"\n/ekp 를 입력하면 업비트: 매도최우선호가, OKX: 매수최우선호가 로 계산한 진입김프를 확인할 수 있으며,"
            body += f"\n/xkp 를 입력하면 업비트: 매수최우선호가, OKX: 매도최우선호가 로 계산한 탈출김프를 확인할 수 있습니다."
            body += f'\n등록된 관심코인이 없는 경우, /kp 로 김프 조회 시, 거래량 기준 상위 20개 코인만 조회됩니다.'
            body += f'\n/addint 명령어를 통해 관심코인을 등록하시면 등록된 코인만 조회할 수 있습니다.'
            body += f'\n\n5. /std 명령어를 이용하면 최근 김프변동성이 높은 코인들을 조회할 수 있습니다.'
            body += f'\n\n6. /addcoin 과 /rmcoin 명령어를 이용하면 개별 코인에 대한 김프 및 테더환산가에 대한 알람 및 자동매매를 설정할 수 있습니다.'
            body += f'\n자세한 사용법은 /addcoin 을 입력하세요.'
            body += f'\n\n7. /plot 과 /plotc 명령어를 이용하면 원하는 코인의 김프차트를 보실 수 있습니다.'
            body += f'\n차트의 모양과 캔들종류도 설정 가능하며, 동시에 여러코인도 차트에 나타낼 수 있습니다.'
            body += f'\n자세한 사용방법은 /plot 과 /plotc 를 입력해서 확인하세요.'
            body += f'\n\n8. /fetch 명령어를 이용하면 김프데이터를 엑셀파일로 받아볼 수 있습니다.'
            body += f'\n자세한 사용법은 /fetch 를 입력하여 확인하세요.'
            body += f'\n\n9. /alarm 명령어를 입력하면 김프알람 횟수와 간격을 설정할 수 있습니다. 자세한 사용법은 /alarm 을 입력하여 확인하세요.'
            body += f"\n\n10. /fundt 명령어를 통해 OKX USDT 선물 펀딩률을 확인할 수 있습니다."
            body += f"\n\n11. /diff 명령어를 통해 거래량가중평균김프와 김프괴리가 심한 코인들을 감지할 수 있습니다."
            body += f'\n\n12. 자동매매와 관련된 기능은 /help2 를 입력하여 확인 해 주세요.'
            body += f"\n\n13. /addcir, /addcoin 사용 시, 설명을 표시하고 싶지 않으신 경우 /omit 을 입력하여 설명을 끄실 수 있습니다."
            body += f'\n\n\n'+u'\U0001F4DE'+'결제관련 문의 및 기타 문의는 텔레그램 @charlie1155로 문의해 주세요.'
            self.bot.send_thread(update.effective_chat.id, body, parse_mode='html')
        help_thread_th = Thread(target=help_thread, daemon=True)
        help_thread_th.start()

    def help2(self, update, context):
        def help2_thread():
            self.get_log('help2', update, context)
            body = f"1. /api_key 명령어를 이용하면 거래소 잔고 확인 및 자동매매를 위한 개인 API key를 등록하실 수 있습니다.\n\n"
            body += f"2. /bal 명령어로 업비트와 OKX의 현재 잔고를 확인할 수 있습니다.\n\n"
            body += f"3. /pos 명령어로 업비트와 OKX의 현재 포지션을 확인할 수 있습니다.\n\n"
            body += f"4. /his 명령어로 자동매매내역을 확인하실 수 있습니다.\n\n"
            body += f"5. /pro 명령어로 자동매매손익을 확인하실 수 있습니다.\n\n"
            body += f"6. /lev 명령어로 업비트 OKX 양방 자동거래 진입 시 적용될 OKX 레버리지를 설정할 수 있습니다.\n\n"
            body += f"7. /enter 명령어로 김프거래에 수동진입할 수 있습니다. 자세한 내용은 /enter 명령어를 입력하여 확인하세요.\n\n"
            body += f"8. /exit 명령어로 김프거래를 수동탈출(정리)할 수 있습니다. 자세한 내용은 /exit 명령어를 입력하여 확인하세요.\n\n"
            body += f"9. /cgh 명령어로 자동매매기능으로 진입되어있는 코인의 탈출김프 혹은 탈출USDT환산가를 변경할 수 있습니다.\n자세한 내용은 /cgh 명령어를 입력하여 확인하세요.\n\n"
            body += f"10. /mar 명령어로 OKX의 마진콜(청산경고) 모니터링을 설정 할 수 있습니다. 자세한 내용은 /mar 을 입력하여 확인하세요.\n\n"
            body += f"11. /safe 명령어로, 자동거래 시 에러로 인해 한쪽 거래소만 체결되는 경우, 정상 체결된 거래소의 포지션을 역매매를 통해 되돌리는 안전장치를 설정할 수 있습니다.\n\n"
            body += f"12. /exd 명령어로, 김프 거래 탈출이 일어나는 달러가격 조건을 설정할 수 있습니다.\n\n"
            body += f"13. 자동매매에 대한 자세한 설명은 /help3 을 입력하여 확인해 주세요."
            body += f'\n\n\n'+u'\U0001F4DE'+'결제관련 문의 및 기타 문의는 텔레그램 @charlie1155로 문의해 주세요.'
            self.bot.send_thread(update.effective_chat.id, body, parse_mode='html')
        help2_thread_th = Thread(target=help2_thread, daemon=True)
        help2_thread_th.start()
    
    def help3(self, update, context):
        def help3_thread():
            self.get_log('help3', update, context)
            body = f"/addcoin 명령어는 단순한 김프알림 설정부터, <b>수동, 반자동매매</b>까지 설정가능한 명령어입니다.\n"
            body += f"<b>수동매매</b>의 경우,\n/addcoin <b>코인심볼, Low%숫자, High%숫자, auto, 투입금액(원)</b> 의 형식으로 설정가능하며,\n"
            body += f"봇이 실시간으로 김프를 감지하여, 설정한 Low 김프에 도달하는 경우 자동으로 업비트 매수, OKX 숏거래로 김프거래에 진입하고,\n"
            body += f"이후, 설정된 High 김프에 도달할때 업비트 매도, OKX 숏정리를 통해 자동으로 김프거래를 탈출(정리) 합니다.\n\n"
            body += f"<b>표준편차자동매매</b>의 경우,\n/addcoin <b>코인심볼, fauto, 표준편차계수(숫자), 투입금액(원)</b> 의 형식으로 설정가능하며,\n"
            body += f"이 경우, 알고리즘이 최근 200분 김프데이터를 바탕으로 선형회귀선을 계산하여 김프의 단기추세를 예측하고 김프변동성(표준편차)을 계산합니다.\n"
            body += f"계산된 단기추세 예측값에 +- (표준편차*표준편차계수)를 하여, 김프의 Low 값과 High 값을 자동으로 설정을 하게 되며,\n표준편차계수를 통해 Low 설정값과 High 설정값 사이의 폭을 조절할 수 있습니다.\n"
            body += f"구체적으로, <b>김프진입의 Low 값은 추세연장선-(최근 200분 표준편차*표준편차계수)</b> 로 계산되며,\n<b>김프탈출의 High 값은 추세연장선+(최근 200분 표준편차*표준편차계수)</b> 로 계산됩니다.\n"
            body += f"따라서, 표준편차계수는 계산된 변동성(표준편차)에 곱해지는 계수이기 때문에,\n 표준편차계수를 높이면, Low 값과 High 값 사이의 폭이 커지고,\n"
            body += f"표준편차계수를 낮추면, Low 값과 High 값 사이의 폭이 작아져 김프의 잔진동에서도 거래를 실행하도록 할 수 있습니다.\n"
            body += f"단순 %가 아닌 표준편차계수를 이용하는 이유는, 코인종류와 시기에 따라 김프변동성이 다르기 때문에 같은 %로 설정하더라도 김프거래가 이루어질 확률이 제각각인데,\n"
            body += f"이러한 거래가 성사될 확률을 표준편차를 이용하여 통일하기 위함입니다.\n"
            body += f"또한 fauto 를 이용하면, 진입과 탈출 설정 값을 자동으로 지정해 주기 때문에, USDT환산가를 이용하여 거래할 때 도움이 됩니다.\n\n"
            body += f"<b>자동(반복)매매</b>의 경우, /addcir 명령어를 이용하여 설정할 수 있습니다.\n"
            body += f"자동(반복)매매에 대한 자세한 설명은 /help4 를 입력하여 확인 해 주세요.\n\n"
            body += f"김프 진입과 탈출에 사용되는 가격은 거래가격이 아닌 <b>매수최우선호가 혹은 매도최우선호가</b>입니다.\n"
            body += f"이는 모니터링 김프와 거래 체결시의 실제 김프간의 괴리를 최소화하기 위한 알고리즘입니다.\n"
            body += f"따라서, 김프거래 진입 시의 김프는 업비트 매도최우선호가와 OKX 매수최우선 호가로 김프를 계산하며,\n"
            body += f"김프거래 탈출 시의 김프는 업비트 매수최우선호가와 OKX 매도최우선 호가로 김프를 계산하여 자동거래를 실행합니다."
            body += f'\n\n\n'+u'\U0001F4DE'+'결제관련 문의 및 기타 문의는 텔레그램 @charlie1155로 문의해 주세요.'
            self.bot.send_thread(update.effective_chat.id, body, parse_mode=telegram.ParseMode.HTML)
        help3_thread_th = Thread(target=help3_thread, daemon=True)
        help3_thread_th.start()
    
    def help4(self, update, context):
        def help4_thread():
            self.get_log('help4', update, context)
            body = f"/addcir 명령어는 /addcoin 기능을 활용하여 자동(반복)매매를 설정하는 명령어 입니다.\n"
            body += f"최초 설정시, /addcir 에 설정값이 등록됨과 동시에, /addcoin 에 해당 설정값을 바탕으로 반자동거래가 자동등록됩니다.\n"
            body += f"이후, 매 3분 마다 김프추세를 추적하며, 김프거래에 진입이 될 때까지 low 와 high 값을 재설정하며 /addcoin 을 자동갱신합니다.\n"
            body += f"진입거래가 끝나고 난 후, /addcoin 이 작동하여 <b>김프거래를 탈출하게 될 때, 봇이 등록된 /addcir 반복매매 설정값을 조회</b>하여\n"
            body += f"자동으로 /addcoin 에 반자동거래를 재등록하게 됩니다.\n"
            body += f"/addcirl 명령어를 이용하면, 특정 김프 이상에서 /addcir 설정을 임시 비활성화 하여, 자동재등록을 제한할 수 있으며,\n"
            body += f"/addcirn 명령어로 /addcir(반복거래) 의 김프거래 최대 싸이클 횟수를 제한할 수 있습니다.\n\n"
            body += f"기본적으로 /addcir 기능은 <b>/addcoin 의 여러 기능들을 모듈로써 활용</b>하는 것이기 때문에,\n"
            body += f"실제 거래는 /addcoin 의 기능을 통해 발생하며, 매 거래 종료시 /addcir 에 등록된 설정값을 읽어들이는 방식으로 작동합니다.\n"
            body += f"따라서, 매 거래 싸이클의 현재상황은 /addcoin 을 통해 조회가 가능하며, 레버리지도 정상적으로 적용됩니다.\n"
            body += f"또한, 이미 /addcoin 에 코인이 등록되어 있는 상태에서도 /addcir 로 자동(반복)매매 등록이 가능합니다.\n"
            body += f"이 경우, /addcoin 에 등록되어 있는 코인이 김프거래에 진입되어 있지 않은(진입대기) 상태면\n"
            body += f"/addcir 설정에 따라 재등록되며, 이미 김프거래에 진입되어 있는(탈출대기) 상태면,\n"
            body += f"기존 /addcoin 설정을 건드리지 않고, /addcir 설정만 등록되어, 탈출완료 상태가 될때까지 모니터링이 시작됩니다.\n"
            body += f"김프거래 싸이클이 반복되면서, 업비트 혹은 OKX측의 잔고가 최초운용금액보다 작아지는 경우,\n"
            body += f"봇이 자동으로 잔고가 더 작은 쪽에 운용금액을 맞추어 /addcoin 을 재등록하게 됩니다.\n"
            body += f"만약, <b>어느 한 거래소의 잔고가 최초운용금액의 1/2 이하가 되는경우, 반복설정이 비활성화</b> 되며 /addcoin 재등록을 중지합니다.\n"
            body += f"OKX의 잔고 계산은 설정된 레버리지를 적용하여 계산됩니다.\n"
            body += f"예를들어, 현재 레버리지가 2배이며, OKX의 잔고가 100만 원 인 경우,\n"
            body += f"실제 계약가능한 포지션금액은 200만 원이기 때문에, 잔고가 200만 원(보유현금*레버리지)로 계산됩니다.\n"
            body += f"자동(반복)매매 설정을 해제하시려면, /rmcir 로 설정을 삭제하세요.\n\n"
            body += f"<b>경고</b>: 자동매매 설정이 등록된 상태에서 김프거래에 진입되어 있는 해당 코인을 /exit 으로 수동탈출하는 경우, 탈출완료로 감지되어 자동재등록이 실행됩니다.\n"
            body += f"이 점 유의하시길 바라며, 자동 재등록을 원하지 않으시면 /rmcir 로 꼭 반복거래 설정을 삭제하여 주시기 바랍니다."
            body += f'\n\n\n'+u'\U0001F4DE'+'결제관련 문의 및 기타 문의는 텔레그램 @charlie1155로 문의해 주세요.'
            self.bot.send_thread(update.effective_chat.id, body, parse_mode=telegram.ParseMode.HTML)
        help4_thread_th = Thread(target=help4_thread, daemon=True)
        help4_thread_th.start()

    def admin_help(self, update, context):
        def admin_help_thread():
            self.get_log('admin_help', update, context,'admin')
            user_id = update.effective_chat.id
            if user_id == self.admin_id:
                body = f"1. /ext user_id, 일수 -> 유저이용기간 연장\n"
                body += f"2. /extall 일수 -> 모든유저 이용기간 연장\n"
                body += f"3. /admin 내용 -> 공지사항 전체 전송\n"
                body += f"4. /resetapi user_id -> 해당 유저 API 초기화\n"
                body += f"5. /restart -> kimp_trading_bot.py 재시작\n"
                body += f"6. /redollar -> update_dollar_thread reinit\n"
                body += f"7. /accrefer user_id,1 -> 해당 유저 레퍼럴 신청 승인/거부\n"
                body += f"8. /server_check -> 서버점검 등록\n"
                body += f"9. /addexec -> 임원 or 영업사원 텔레그램 ID 등록 (쿠폰발급용)"

                self.bot.send_thread(user_id, body)
                return
        admin_help_thread_th = Thread(target=admin_help_thread, daemon=True)
        admin_help_thread_th.start()

    def api_key(self, update, context):
        def api_key_thread():
            self.get_log('api_key', update, context)
            # Payment check
            user_id = update.effective_chat.id
            auth = self.authorize(user_id)
            if auth is False:
                return
            try:
                input_msg = ''.join(context.args).split(',')
                if context.args == []:
                    # Load registered api keys
                    number_of_user_upbit_keys = len(self.snatcher.user_api_key_df[(self.snatcher.user_api_key_df['exchange']=='UPBIT')&(self.snatcher.user_api_key_df['user_id']==user_id)])
                    number_of_user_okx_keys = len(self.snatcher.user_api_key_df[(self.snatcher.user_api_key_df['exchange']=='OKX')&(self.snatcher.user_api_key_df['user_id']==user_id)])

                    body = f"거래소 잔고 조회 및 자동매매 API 요청을 위한 API key를 등록하는 명령어 입니다.\n"
                    body += f"API key 등록 시, IP: xxx.xxx.xxx.xxx 로부터의 접근을 허가 해 주세요.\n"
                    body += f"IP 주소는 관리자 (@charlie1155) 에게 요청 시 제공해 드립니다.\n\n"
                    body += f"<b>거래소 이름(okx 혹은 upbit)</b>, <b>API Access키</b>, <b>API Secret키</b> 순서로 콤마(,)로 구분하여 입력해 주세요.\n"
                    body += f"OKX 거래소의 경우에는 passphrase 도 요구되므로, API Access키, API Secret키, passphrase 순서로 입력해 주세요.\n"
                    body += f"ex1) /api_key upbit, AbsdfasfwaeCd1234, Bfadsfawefdsfawefagds123\n"
                    body += f"ex2) /api_key okx, zwdsasfdaefasdfce52, Ekduadsfaewfawbasdf12, 123123123\n\n"
                    body += f"<b>API 키는 업비트와 OKX 각각 1개 이상 등록</b>하여야 이용이 가능하며,\n"
                    body += f"API 요청을 쪼개어 전송하기 위한 목적으로 2개 이상의 API 키도 등록이 가능합니다.\n"
                    body += f"이 때 업비트와 OKX의 API 키 갯수가 일치할 필요는 없습니다.\n"
                    body += f"즉, 3개의 업비트 API키를 등록하고, 1개의 OKX API키만 등록하는 것도 가능합니다.\n"
                    body += f"<b>한 번 등록하신 API 키는 보안을 위해 암호화되며, 수정하시거나 다시 조회하실 수 없습니다.</b>\n"
                    body += f"자세한 등록방법은 https://charlietrip.tistory.com/17 을 참고하시기 바랍니다.\n"
                    body += f"등록된 API 키 삭제를 원하시는 경우, <b>/reset_api_key</b> 명령어를 참고하세요.\n\n"
                    body += f"<b>현재 등록된 API 상태</b>\n"
                    body += f"업비트: {number_of_user_upbit_keys}개\n"
                    body += f"OKX: {number_of_user_okx_keys}개"
                    self.bot.send_thread(chat_id=user_id, text=body, parse_mode=telegram.ParseMode.HTML)
                    return
                elif len(input_msg) != 3:
                    body = f"올바른 입력이 아닙니다. /api_key 를 입력하여 사용방법을 확인 해 주세요."
                    self.bot.send_thread(chat_id=user_id, text=body, parse_mode=telegram.ParseMode.HTML)
                    return

                input_exchange = str(input_msg[0]).upper()
                if input_exchange not in ['OKX', 'UPBIT']:
                    body = f"거래소 명은 okx 혹은 upbit 만 입력가능합니다.\n"
                    body += f"/api_key 를 입력하여 사용방법을 확인 해 주세요."
                    self.bot.send_thread(user_id, body)
                    return
                
                input_access_key = input_msg[1]
                input_secret_key = input_msg[2]
                if input_exchange == 'OKX':
                    input_passphrase = input_msg[3]
                else:
                    input_passphrase = None

                # Check if there's already registerd api keys
                number_of_existing_keys = len(self.snatcher.user_api_key_df[(self.snatcher.user_api_key_df['access_key']==input_access_key)&(self.snatcher.user_api_key_df['user_id']==user_id)])
                if number_of_existing_keys != 0:
                    body = f"이미 등록된 동일한 API 키가 있습니다.\n"
                    body += f"등록된 API는 수정하실 수 없으며, 삭제를 원하시는 경우, /reset_api_key 명령어를 참고하세요."
                    self.bot.send_thread(user_id, body)
                    return

                # Check API key
                if input_exchange == 'UPBIT':
                    integrity_flag, message = self.upbit_adaptor.check_upbit_api_key(input_access_key, input_secret_key)
                    if integrity_flag == False:
                        body = f"유효하지 않은 업비트 API Key 입니다.\n"
                        body += f"API Key 등록이 취소되었습니다.\n"
                        body += f"Error: {message}\n"
                        body += f"API 실행 허용IP가 정상적으로 설정되지 않았거나, access key 와 secret key 가 정확하게 입력되지 않았을 수 있습니다.\n"
                        body += f"자세한 문의사항은 @charlie1155 로 문의 해 주세요."
                        self.bot.send_thread(user_id, body)
                        return
                elif input_exchange == 'OKX':
                    integrity_flag, message = self.okx_adaptor.check_okx_api_key(input_access_key, input_secret_key, input_passphrase)
                    if integrity_flag == False:
                        body = f"유효하지 않은 OKX API Key 입니다.\n"
                        body += f"API Key 등록이 취소되었습니다.\n"
                        body += f"Error: {message}\n"
                        body += f"API 실행 허용IP가 정상적으로 설정되지 않았거나, access key 와 secret key 가 정확하게 입력되지 않았을 수 있습니다.\n"
                        body += f"자세한 문의사항은 @charlie1155 로 문의 해 주세요."
                        self.bot.send_thread(user_id, body)
                        return

                # Passed validation
                db_client = InitDBClient(**self.local_db_dict)
                sql = """
                INSERT INTO user_api_key
                (user_id, exchange, access_key, secret_key)
                VALUES (%s, %s, HEX(AES_ENCRYPT(%s, SHA2('{encryption_key}', 256))), HEX(AES_ENCRYPT(%s, SHA2('{encryption_key}', 256))))
                """.format(encryption_key=self.encryption_key)
                val = [user_id, input_exchange, input_access_key, input_secret_key]
                db_client.curr.execute(sql, val)
                db_client.conn.commit()
                db_client.conn.close()
                body = f"{input_exchange}의 API KEY가 정상적으로 등록 되었습니다.\n"
                self.bot.send_thread(chat_id=user_id, text=body)
                return
            except Exception as e:
                self.telegram_bot_logger.error(f"api_key|{traceback.format_exc()}")
                body = f"서비스에 불편을 드려 죄송합니다. 일시적인 오류가 발생했습니다. 관리자에게 문의 해 주세요. (@charlie1155)\n"
                body += f"error: {e}"
                self.bot.send_thread(chat_id=user_id, text=body)
                return
        api_key_thread_th = Thread(target=api_key_thread, daemon=True)
        api_key_thread_th.start()

    def reset_api_key(self, update, context):
        def reset_api_key_thread():
            self.get_log('reset_api_key', update, context)
            # Payment check
            user_id = update.effective_chat.id
            auth = self.authorize(user_id)
            if auth is False:
                return
            try:
                input_msg = ''.join(context.args).split(',')
                if context.args == []:
                    # Load registered api keys
                    number_of_user_upbit_keys = len(self.snatcher.user_api_key_df[self.snatcher.user_api_key_df['exchange']=='UPBIT'])
                    number_of_user_okx_keys = len(self.snatcher.user_api_key_df[self.snatcher.user_api_key_df['exchange']=='OKX'])

                    body = f"등록된 거래소 API 키를 삭제하는 명령어 입니다.\n"
                    body += f"/reset_api_key 거래소이름 형식으로 입력 해 주세요.\n"
                    body += f"ex1) /reset_api_key upbit\n"
                    body += f"ex2) /reset_api_key okx\n"
                    body += f"개별 API 키 삭제는 불가능하며, 거래소 별 전체 API Key 삭제만 가능합니다.\n\n"
                    body += f"<b>현재 등록된 API 상태</b>\n"
                    body += f"업비트: {number_of_user_upbit_keys}개\n"
                    body += f"OKX: {number_of_user_okx_keys}개"
                    self.bot.send_thread(chat_id=user_id, text=body, parse_mode=telegram.ParseMode.HTML)
                    return
                elif len(input_msg) != 1:
                    body = f"올바른 입력이 아닙니다. /reset_api_key 를 입력하여 사용방법을 확인 해 주세요."
                    self.bot.send_thread(chat_id=user_id, text=body, parse_mode=telegram.ParseMode.HTML)
                    return

                input_exchange = str(input_msg[0]).upper()
                if input_exchange not in ['OKX', 'UPBIT']:
                    body = f"거래소 명은 okx 혹은 upbit 만 입력가능합니다.\n"
                    body += f"/api_key 를 입력하여 사용방법을 확인 해 주세요."
                    self.bot.send_thread(user_id, body)
                    return
                
                # Passed validation
                db_client = InitDBClient(**self.local_db_dict)
                sql = """DELETE FROM user_api_key WHERE user_id=%s AND exchange=%s"""
                val = [user_id, input_exchange]
                db_client.curr.execute(sql, val)
                db_client.conn.commit()
                db_client.conn.close()
                time.sleep(1.5)
                body = f"{input_exchange}의 API KEY가 정상적으로 삭제되었습니다.\n"
                self.bot.send_thread(chat_id=user_id, text=body)
                return
            except Exception as e:
                self.telegram_bot_logger.error(f"reset_api_key|{traceback.format_exc()}")
                body = f"서비스에 불편을 드려 죄송합니다. 일시적인 오류가 발생했습니다. 관리자에게 문의 해 주세요. (@charlie1155)\n"
                body += f"error: {e}"
                self.bot.send_thread(chat_id=user_id, text=body)
                return
        reset_api_key_thread_th = Thread(target=reset_api_key_thread, daemon=True)
        reset_api_key_thread_th.start()

    def kp(self, update, context, show_krw=False):
        def kp_thread():
            self.get_log('kp', update, context)
            # Payment check
            user_id = update.effective_chat.id
            auth = self.authorize(user_id)
            if auth is False:
                return
            try:
                # Load dollar info
                dollar = self.get_dollar_dict()['price']

                body_kimp = u'\U0001F4CC'+f'업비트 대 OKX USDT선물 (달러: {krw(dollar)})\n'
                # if server check is on going, don't show the kimp
                if self.upbit_server_check==True or self.okx_server_check==True:
                    if self.upbit_server_check==True:
                        temp_str = " 업비트"
                    else:
                        temp_str = ""
                    if self.okx_server_check==True:
                        temp_str2 = " OKX"
                    else:
                        temp_str2 = ""
                    body_kimp += f"현재{temp_str}{temp_str2} 서버 점검 중 입니다."
                    self.bot.send_thread(chat_id=user_id, text=body_kimp)
                    return
                # merge okx and upbit 24hr ticker
                merged_df = self.get_kimp_df()
                merged_df = merged_df.sort_values('acc_trade_price_24h', ascending=False).reset_index(drop=True)

                wa_kimp_dict = self.get_wa_kimp_dict()
                weighted_avg_kimp = wa_kimp_dict['wa_kimp']
                weighted_avg_usdt = wa_kimp_dict['wa_usdt']

                body_kimp += f"거래량 가중평균 김프: {round(weighted_avg_kimp*100,3)}%\n"
                body_kimp += f"거래량 가중평균 테더환산가: {round(weighted_avg_usdt,2)}원\n\n"
                # See if there's already listed interset coins
                db_client = InitDBClient(**self.local_db_dict)
                db_client.curr.execute("""SELECT interest_coin FROM user_info WHERE user_id=%s""", user_id)
                fetched_interest_coin_str = db_client.curr.fetchall()[0]['interest_coin']
                db_client.conn.close()

                # if there's no listed coins, just show top 20 coins
                if fetched_interest_coin_str == None:
                    merged_df = merged_df.head(20)
                else:
                    interest_coin_list = fetched_interest_coin_str.split(',')
                    merged_df = merged_df[merged_df['symbol'].isin(interest_coin_list)].reset_index(drop=True)

                for row_tup in merged_df.iterrows():
                        index = row_tup[0] + 1
                        row = row_tup[1]
                        signed_change_rate = round(row['signed_change_rate']*100,2)
                        if signed_change_rate > 0:
                            temp_str = '+'
                        else:
                            temp_str = ''
                        body_kimp += f"<b>{row['symbol']}</b>|<b>김프:{round(row['tp_kimp']*100,3)}%</b>|<b>테더환산:{round(row['tp_usdt'],1)}</b>\n"
                        if show_krw:
                            body_kimp += f"업비트:{krw(round(row['trade_price']))}원({temp_str}{signed_change_rate}%), OKX:{krw(round(row['okx_last_price']*dollar))}원\n"
                        else:
                            body_kimp += f"업비트:{krw(round(row['trade_price']))}원({temp_str}{signed_change_rate}%), OKX:{round(row['okx_last_price'],3)}USD\n"

                self.bot.send_thread(chat_id=user_id, text=body_kimp, parse_mode=telegram.ParseMode.HTML)
            except Exception as e:
                self.telegram_bot_logger.error(f"kp|{traceback.format_exc()}")
                body = f"서비스에 불편을 드려 죄송합니다. 일시적인 오류가 발생했습니다. 관리자에게 문의 해 주세요. (@charlie1155)\n"
                body += f"error: {e}"
                self.bot.send_thread(chat_id=user_id, text=body)
                return
        kp_thread_th = Thread(target=kp_thread, daemon=True)
        kp_thread_th.start()
    
    def ekp(self, update, context, show_krw=False):
        def ekp_thread():
            self.get_log('ekp', update, context)
            # Payment check
            user_id = update.effective_chat.id
            auth = self.authorize(user_id)
            if auth is False:
                return
            try:
                # Load dollar info
                dollar = self.get_dollar_dict()['price']

                body_kimp = u'\U0001F4CC'+f'업비트 대 OKX USDT선물 (달러: {krw(dollar)})\n'
                # if server check is on going, don't show the kimp
                if self.upbit_server_check==True or self.okx_server_check==True:
                    if self.upbit_server_check==True:
                        temp_str = " 업비트"
                    else:
                        temp_str = ""
                    if self.okx_server_check==True:
                        temp_str2 = " OKX"
                    else:
                        temp_str2 = ""
                    body_kimp += f"현재{temp_str}{temp_str2} 서버 점검 중 입니다."
                    self.bot.send_thread(chat_id=user_id, text=body_kimp)
                    return
                # merge okx and upbit 24hr ticker
                merged_df = self.get_kimp_df()
                merged_df = merged_df.sort_values('acc_trade_price_24h', ascending=False).reset_index(drop=True)

                wa_kimp_dict = self.get_wa_kimp_dict(kimp_side='enter')
                weighted_avg_kimp = wa_kimp_dict['wa_kimp']
                weighted_avg_usdt = wa_kimp_dict['wa_usdt']

                body_kimp += f"거래량 가중평균 진입김프: {round(weighted_avg_kimp*100,3)}%\n"
                body_kimp += f"거래량 가중평균 진입테더: {round(weighted_avg_usdt,2)}원\n\n"
                # See if there's already listed interset coins
                db_client = InitDBClient(**self.local_db_dict)
                db_client.curr.execute("""SELECT interest_coin FROM user_info WHERE user_id=%s""", user_id)
                fetched_interest_coin_str = db_client.curr.fetchall()[0]['interest_coin']
                db_client.conn.close()

                # if there's no listed coins, just show top 20 coins
                if fetched_interest_coin_str == None:
                    merged_df = merged_df.head(20)
                else:
                    interest_coin_list = fetched_interest_coin_str.split(',')
                    merged_df = merged_df[merged_df['symbol'].isin(interest_coin_list)].reset_index(drop=True)

                for row_tup in merged_df.iterrows():
                        index = row_tup[0] + 1
                        row = row_tup[1]
                        signed_change_rate = round(row['signed_change_rate']*100,2)
                        if signed_change_rate > 0:
                            temp_str = '+'
                        else:
                            temp_str = ''
                        body_kimp += f"<b>{row['symbol']}</b>|<b>진입김프:{round(row['enter_kimp']*100,3)}%</b>|<b>진입테더환산:{round(row['enter_usdt'],1)}</b>\n"
                        if show_krw:
                            body_kimp += f"업비트:{krw(round(row['upbit_ask_price']))}원({temp_str}{signed_change_rate}%), OKX:{krw(round(row['okx_bid_price']*dollar))}원\n"
                        else:
                            body_kimp += f"업비트:{krw(round(row['upbit_ask_price']))}원({temp_str}{signed_change_rate}%), OKX:{round(row['okx_bid_price'],3)}USD\n"

                self.bot.send_thread(chat_id=user_id, text=body_kimp, parse_mode=telegram.ParseMode.HTML)
            except Exception as e:
                self.telegram_bot_logger.error(f"ekp|{traceback.format_exc()}")
                body = f"서비스에 불편을 드려 죄송합니다. 일시적인 오류가 발생했습니다. 관리자에게 문의 해 주세요. (@charlie1155)\n"
                body += f"error: {e}"
                self.bot.send_thread(chat_id=user_id, text=body)
                return
        ekp_thread_th = Thread(target=ekp_thread, daemon=True)
        ekp_thread_th.start()

    def xkp(self, update, context, show_krw=False):
        def xkp_thread():
            self.get_log('xkp', update, context)
            # Payment check
            user_id = update.effective_chat.id
            auth = self.authorize(user_id)
            if auth is False:
                return
            try:
                # Load dollar info
                dollar = self.get_dollar_dict()['price']

                body_kimp = u'\U0001F4CC'+f'업비트 대 OKX USDT선물 (달러: {krw(dollar)})\n'
                # if server check is on going, don't show the kimp
                if self.upbit_server_check==True or self.okx_server_check==True:
                    if self.upbit_server_check==True:
                        temp_str = " 업비트"
                    else:
                        temp_str = ""
                    if self.okx_server_check==True:
                        temp_str2 = " OKX"
                    else:
                        temp_str2 = ""
                    body_kimp += f"현재{temp_str}{temp_str2} 서버 점검 중 입니다."
                    self.bot.send_thread(chat_id=user_id, text=body_kimp)
                    return
                # merge okx and upbit 24hr ticker
                merged_df = self.get_kimp_df()
                merged_df = merged_df.sort_values('acc_trade_price_24h', ascending=False).reset_index(drop=True)

                wa_kimp_dict = self.get_wa_kimp_dict(kimp_side='exit')
                weighted_avg_kimp = wa_kimp_dict['wa_kimp']
                weighted_avg_usdt = wa_kimp_dict['wa_usdt']

                body_kimp += f"거래량 가중평균 탈출김프: {round(weighted_avg_kimp*100,3)}%\n"
                body_kimp += f"거래량 가중평균 탈출테더: {round(weighted_avg_usdt,2)}원\n\n"
                # See if there's already listed interset coins
                db_client = InitDBClient(**self.local_db_dict)
                db_client.curr.execute("""SELECT interest_coin FROM user_info WHERE user_id=%s""", user_id)
                fetched_interest_coin_str = db_client.curr.fetchall()[0]['interest_coin']
                db_client.conn.close()

                # if there's no listed coins, just show top 20 coins
                if fetched_interest_coin_str == None:
                    merged_df = merged_df.head(20)
                else:
                    interest_coin_list = fetched_interest_coin_str.split(',')
                    merged_df = merged_df[merged_df['symbol'].isin(interest_coin_list)].reset_index(drop=True)

                for row_tup in merged_df.iterrows():
                        index = row_tup[0] + 1
                        row = row_tup[1]
                        signed_change_rate = round(row['signed_change_rate']*100,2)
                        if signed_change_rate > 0:
                            temp_str = '+'
                        else:
                            temp_str = ''
                        body_kimp += f"<b>{row['symbol']}</b>|<b>탈출김프:{round(row['exit_kimp']*100,3)}%</b>|<b>탈출테더환산:{round(row['exit_usdt'],1)}</b>\n"
                        if show_krw:
                            body_kimp += f"업비트:{krw(round(row['upbit_bid_price']))}원({temp_str}{signed_change_rate}%), OKX:{krw(round(row['okx_ask_price']*dollar))}원\n"
                        else:
                            body_kimp += f"업비트:{krw(round(row['upbit_bid_price']))}원({temp_str}{signed_change_rate}%), OKX:{round(row['okx_ask_price'],3)}USD\n"

                self.bot.send_thread(chat_id=user_id, text=body_kimp, parse_mode=telegram.ParseMode.HTML)
            except Exception as e:
                self.telegram_bot_logger.error(f"xkp|{traceback.format_exc()}")
                body = f"서비스에 불편을 드려 죄송합니다. 일시적인 오류가 발생했습니다. 관리자에게 문의 해 주세요. (@charlie1155)\n"
                body += f"error: {e}"
                self.bot.send_thread(chat_id=user_id, text=body)
                return
        xkp_thread_th = Thread(target=xkp_thread, daemon=True)
        xkp_thread_th.start()
    
    def bal(self, update, context):
        def bal_thread():
            self.get_log('bal', update, context)
            # Payment check
            user_id = update.effective_chat.id
            auth = self.authorize(user_id)
            if auth is False:
                return
            try:
                try:
                    user_upbit_access_key, user_upbit_secret_key = self.snatcher.user_api_key_df[(self.snatcher.user_api_key_df['user_id']==user_id)&(self.snatcher.user_api_key_df['exchange']=='UPBIT')]\
                    .sample(n=1)[['access_key', 'secret_key']].values[0]
                    user_okx_access_key, user_okx_secret_key, user_okx_passphrase = self.snatcher.user_api_key_df[(self.snatcher.user_api_key_df['user_id']==user_id)&(self.snatcher.user_api_key_df['exchange']=='OKX')]\
                    .sample(n=1)[['access_key', 'secret_key', 'passphrase']].values[0]
                except Exception:
                    body = f"등록된 API 키가 없어 거래소와 통신이 불가능합니다.\n"
                    body += f"/api_key 명령어를 이용하여 업비트와 OKX의 API 키를 등록해 주세요."
                    self.bot.send_thread(chat_id=user_id, text=body)
                    return
                
                upbit_return_dict = {}
                upbit_balance_df_thread = Thread(target=self.upbit_adaptor.upbit_all_position_information, args=(user_upbit_access_key, user_upbit_secret_key, upbit_return_dict), daemon=True)
                upbit_balance_df_thread.start()
                upbit_return_dict2 = {}
                upbit_all_ticker_thread = Thread(target=self.upbit_adaptor.upbit_all_ticker, args=(user_upbit_access_key, user_upbit_secret_key, upbit_return_dict2), daemon=True)
                upbit_all_ticker_thread.start()
                # okx_return_dict = {}
                # okx_all_position_information_thread = Thread(target=self.okx_adaptor.okx_position_information, args=(user_okx_access_key, user_okx_secret_key, user_okx_passphrase, okx_return_dict), daemon=True)
                # okx_all_position_information_thread.start()
                okx_trade_balance_df = self.okx_adaptor.get_okx_trade_balance(user_okx_access_key, user_okx_secret_key, user_okx_passphrase)
                upbit_balance_df_thread.join()
                upbit_all_ticker_thread.join()
                # okx_all_position_information_thread.join()
                upbit_all_ticker_df = upbit_return_dict2['res']
                upbit_balance_df = pd.DataFrame(upbit_return_dict['res']['result'])
                upbit_balance_df.loc[:, 'balance':'avg_buy_price'] = upbit_balance_df.loc[:, 'balance':'avg_buy_price'].astype(float)
                upbit_balance_df['market'] = 'KRW-' + upbit_balance_df['currency']
                upbit_balance_df = upbit_balance_df.merge(upbit_all_ticker_df[['market','trade_price']], how='left', on='market')
                upbit_balance_df.loc[upbit_balance_df['currency']=='KRW', 'trade_price'] = 1
                upbit_balance_df['entered_krw'] = upbit_balance_df['balance'] * upbit_balance_df['avg_buy_price']
                upbit_balance_df['locked_krw'] = upbit_balance_df['locked'] * upbit_balance_df['avg_buy_price']
                upbit_krw_balance = upbit_balance_df[upbit_balance_df['currency']=='KRW']['balance'].iloc[0]
                upbit_total_entered_krw = upbit_balance_df['entered_krw'].sum()+upbit_balance_df['locked_krw'].sum()
                upbit_total_krw_after_pnl = (((upbit_balance_df['balance'] + upbit_balance_df['locked']) * upbit_balance_df['trade_price'])).sum()

                okx_trading_usdt_account = okx_trade_balance_df[okx_trade_balance_df['ccy']=='USDT']
                okx_available_usdt = okx_trading_usdt_account['availEq'].values[0]
                okx_before_usdt = okx_trading_usdt_account['eq'].values[0] - okx_trading_usdt_account['upl'].values[0]
                okx_entered_usdt = okx_trading_usdt_account['eq'].values[0]-okx_available_usdt
                okx_total_asset_after_pnl = okx_trading_usdt_account['eq'].values[0]
                merged_df = self.get_kimp_df()
                # weighted avg of kimp from BTC, XRP, EOS, XLM
                filtered_df = merged_df[merged_df['symbol'].isin(['BTC','XRP','EOS','XLM'])]
                weighted_avg_kimp = (filtered_df['tp_kimp']*(filtered_df['acc_trade_price_24h']/filtered_df['acc_trade_price_24h'].sum())).sum()
                dollar = self.get_dollar_dict()['price']

                # okx_pos_dict = okx_return_dict['res']

                body = f"<b>거래소 잔고</b>\n"
                body += f"달러환율: {krw(round(dollar, 1))}원\n"
                body += f"송금코인(XRP,EOS,XLM,BTC) 평균김프: <b>{round(weighted_avg_kimp*100,3)}%</b>\n\n"
                body += f"업비트(사용가능): <b>{krw(round(upbit_krw_balance))}</b>원\n"
                body += f"업비트(진입됨): <b>{krw(round(upbit_total_entered_krw))}</b>원\n"
                body += f"업비트(진입기준 총자산): <b>{krw(round(upbit_krw_balance+upbit_total_entered_krw))}</b>원\n"
                body += f"업비트(평가 총자산): <b>{krw(round(upbit_total_krw_after_pnl))}</b>원\n\n"
                body += f"OKX선물(사용가능): <b>{round(okx_available_usdt,3)}</b>USDT\n"
                body += f"OKX선물(진입됨): <b>{round(okx_entered_usdt,3)}</b>USDT\n"
                body += f"OKX선물(진입기준 총자산): <b>{round(okx_before_usdt,3)}</b>USDT\n"
                body += f"OKX선물(평가 총자산): <b>{round(okx_total_asset_after_pnl,3)}</b>USDT\n\n"
                # body += f"OKX BNB:{binance_bnb_balance}BNB\n"
                # body += f"OKX BUSD:{binance_busd_balance}BUSD\n"
                body += f"환율 적용 후 OKX(사용가능): <b>{krw(round(dollar*okx_available_usdt))}</b>원\n"
                body += f"환율 적용 후 OKX(진입됨): <b>{krw(round(dollar*okx_entered_usdt))}</b>원\n"
                body += f"환율 적용 후 OKX(진입기준 총자산): <b>{krw(round(dollar*okx_before_usdt))}</b>원\n"
                body += f"환율 적용 후 OKX(평가 총자산): <b>{krw(round(dollar*okx_total_asset_after_pnl))}</b>원\n"
                body += f"김프,환율 적용 후 OKX(사용가능): <b>{krw(round(dollar*okx_available_usdt*(1+weighted_avg_kimp)))}</b>원\n"
                body += f"김프,환율 적용 후 OKX(진입됨): <b>{krw(round(dollar*okx_entered_usdt*(1+weighted_avg_kimp)))}</b>원\n"
                body += f"김프,환율 적용 후 OKX(진입기준 총자산): <b>{krw(round(dollar*okx_before_usdt*(1+weighted_avg_kimp)))}</b>원\n"
                body += f"김프,환율 적용 후 OKX(평가 총자산): <b>{krw(round(dollar*(okx_total_asset_after_pnl)*(1+weighted_avg_kimp)))}</b>원\n\n"
                body += f"환율 적용 후 양측 진입기준 총자산: <b>{krw(round(upbit_krw_balance+upbit_total_entered_krw+dollar*okx_before_usdt))}</b>원\n"
                body += f"환율 적용 후 양측 평가 총자산: <b>{krw(round(upbit_total_krw_after_pnl+dollar*okx_total_asset_after_pnl))}</b>원\n"
                body += f"김프,환율 적용 후 양측 진입기준 총자산: <b>{krw(round(upbit_krw_balance+upbit_total_entered_krw+dollar*(okx_before_usdt)*(1+weighted_avg_kimp)))}</b>원\n"
                body += f"김프,환율 적용 후 양측 평가 총자산: <b>{krw(round(upbit_total_krw_after_pnl+dollar*(okx_total_asset_after_pnl)*(1+weighted_avg_kimp)))}</b>원"
                self.bot.send_thread(chat_id=user_id, text=body, parse_mode=telegram.ParseMode.HTML)
                return
            except Exception as e:
                self.telegram_bot_logger.error(f"bal|{traceback.format_exc()}")
                e_msg = str(e)
                if 'API' in e_msg:
                    body = f"잘못된 API key 입니다.\n/api_key 를 입력하여 올바른 API Key를 등록하여 주세요."
                    self.bot.send_thread(chat_id=user_id, text=body)
                    return
                else:
                    body = f"서비스에 불편을 드려 죄송합니다. 일시적인 오류가 발생했습니다. 관리자에게 문의 해 주세요. (@charlie1155)\n"
                    body += f"error: {e}"
                    self.bot.send_thread(chat_id=user_id, text=body)
                    return
        bal_thread_th = Thread(target=bal_thread, daemon=True)
        bal_thread_th.start()
    
    def pos(self, update, context):
        def pos_thread():
            self.get_log('pos', update, context)
            # Payment check
            user_id = update.effective_chat.id
            auth = self.authorize(user_id)
            if auth is False:
                return
            try:
                try:
                    user_upbit_access_key, user_upbit_secret_key = self.snatcher.user_api_key_df[(self.snatcher.user_api_key_df['user_id']==user_id)&(self.snatcher.user_api_key_df['exchange']=='UPBIT')]\
                    .sample(n=1)[['access_key', 'secret_key']].values[0]
                    user_okx_access_key, user_okx_secret_key, user_okx_passphrase = self.snatcher.user_api_key_df[(self.snatcher.user_api_key_df['user_id']==user_id)&(self.snatcher.user_api_key_df['exchange']=='OKX')]\
                    .sample(n=1)[['access_key', 'secret_key', 'passphrase']].values[0]
                except Exception:
                    body = f"등록된 API 키가 없어 거래소와 통신이 불가능합니다.\n"
                    body += f"/api_key 명령어를 이용하여 업비트와 OKX의 API 키를 등록해 주세요."
                    self.bot.send_thread(chat_id=user_id, text=body)
                    return

                upbit_all_position_df = self.upbit_adaptor.upbit_all_position_information(user_upbit_access_key, user_upbit_secret_key)
                upbit_all_position_df = upbit_all_position_df[~upbit_all_position_df['currency'].isin(['KRW','USDT'])].reset_index(drop=True)
                upbit_all_position_df['temp_currency'] = upbit_all_position_df['currency'].apply(lambda x: x+'-USDT-SWAP')
                okx_position_dict = self.okx_adaptor.okx_position_information(user_okx_access_key, user_okx_secret_key, user_okx_passphrase)
                okx_total_position_df = pd.DataFrame(okx_position_dict('total'))
                merged_df = okx_total_position_df.merge(upbit_all_position_df, how='outer', left_on='instId', right_on='temp_currency')
                merged_df = merged_df.where(merged_df.notnull(), None)

                body = f"<b>현재 보유 포지션</b>\n"
                
                i = 0
                for row_tup in merged_df.iterrows():
                    row = row_tup[1]
                    okx_symbol = row['instId']
                    okx_qty = row['qty']
                    if okx_qty == 0:
                        okx_side = ''
                    elif okx_qty < 0:
                        okx_side = "숏"
                    else:
                        okx_side = "롱"
                    upbit_symbol = row['currency']
                    if row['balance'] != None:
                        upbit_qty = row['balance'] + row['locked']
                    else:
                        upbit_qty = 0
                    i += 1

                    body += f"\n{i+1}. OKX: {okx_symbol}|{okx_qty}({okx_side}) 개, 업비트: {upbit_symbol}|{round(upbit_qty,3)} 개"
                self.bot.send_thread(chat_id=user_id, text=body, parse_mode=telegram.ParseMode.HTML)
            except Exception as e:
                self.telegram_bot_logger.error(f"pos|{traceback.format_exc()}")
                body = f"서비스에 불편을 드려 죄송합니다. 일시적인 오류가 발생했습니다. 관리자에게 문의 해 주세요. (@charlie1155)\n"
                body += f"error: {e}"
                self.bot.send_thread(chat_id=user_id, text=body)
                return
        pos_thread_th = Thread(target=pos_thread, daemon=True)
        pos_thread_th.start()

    def addint(self, update, context):
        def addint_thread():
            self.get_log('addint', update, context)
            # Payment check
            user_id = update.effective_chat.id
            auth = self.authorize(user_id)
            if auth is False:
                return
            try:
                input_msg = ''.join(context.args).split(',')
                input_msg = [x.upper() for x in input_msg]

                # Fetch already stored interest coin from db
                db_client = InitDBClient(**self.local_db_dict)
                db_client.curr.execute("""SELECT interest_coin FROM user_info WHERE user_id=%s""", user_id)
                fetched_interest_coin = db_client.curr.fetchall()[0]['interest_coin']

                if fetched_interest_coin == None:
                    temp_str = '없음'
                else:
                    temp_str = fetched_interest_coin

                if context.args == []:
                    if self.snatcher.userinfo_df[self.snatcher.userinfo_df['user_id']==user_id]['on_off'].values[0] == 1:
                        body = f"관심코인을 등록하는 명령어입니다.\n/addint 코인심볼 형태로 입력 해 주세요.\n"
                        body += f"관심코인을 등록하면 김프 조회시 (/kp) 관심코인의 김프만 표시됩니다.\n"
                        body += f"여러 코인을 동시에 등록하실 수 있으며 등록삭제는 /rmint 명령어를 이용 해 주세요.\n"
                        body += f"ex1) /addint btc,eth,xrp\n\n"
                    else:
                        body = ""
                    body += f"<b>현재 등록된 관심코인: {temp_str}</b>"
                    self.bot.send_thread(chat_id=user_id, text=body, parse_mode=telegram.ParseMode.HTML)
                    db_client.conn.close()
                    return
                
                for input_coin in input_msg:
                    if input_coin not in [x.replace('-USDT-SWAP','') for x in self.get_both_listed_okx_symbols()]:
                        body = f"{input_coin}는 상장되지 않은 코인입니다.\n"
                        body += f"업비트와 OKX 선물시장에 동시상장된 코인만 등록이 가능합니다."
                        self.bot.send_thread(chat_id=user_id, text=body)
                        db_client.conn.close()
                        return

                if fetched_interest_coin == None:
                    input_coin_list = list(set(input_msg))
                    input_coin_list_str = ','.join(input_coin_list)
                    db_client.curr.execute("""UPDATE user_info SET interest_coin=%s WHERE user_id=%s""", (input_coin_list_str, user_id))
                    db_client.conn.commit()
                    body = f"{input_coin_list_str}가 관심코인으로 등록되었습니다.\n\n"
                    body += f"<b>현재 등록된 관심코인: {input_coin_list_str}</b>"
                    self.bot.send_thread(chat_id=user_id, text=body, parse_mode=telegram.ParseMode.HTML)
                else:
                    fetched_interest_coin_list = fetched_interest_coin.split(',')
                    new_interest_coin_list = list(set(fetched_interest_coin_list + input_msg))
                    new_interest_coin_list_str = ','.join(new_interest_coin_list)
                    db_client.curr.execute("""UPDATE user_info SET interest_coin=%s WHERE user_id=%s""", (new_interest_coin_list_str, user_id))
                    db_client.conn.commit()
                    body = f"{','.join(list(set(input_msg)))}가 관심코인으로 등록되었습니다.\n\n"
                    body += f"<b>현재 등록된 관심코인: {new_interest_coin_list_str}</b>"
                    self.bot.send_thread(chat_id=user_id, text=body, parse_mode=telegram.ParseMode.HTML)
                db_client.conn.close()
                return
            except Exception as e:
                self.telegram_bot_logger.error(f"addint|{traceback.format_exc()}")
                body = f"서비스에 불편을 드려 죄송합니다. 일시적인 오류가 발생했습니다. 관리자에게 문의 해 주세요. (@charlie1155)\n"
                body += f"error: {e}"
                self.bot.send_thread(chat_id=user_id, text=body)
                return
        addint_thread_th = Thread(target=addint_thread, daemon=True)
        addint_thread_th.start()
    
    def rmint(self, update, context):
        def rmint_thread():
            self.get_log('rmint', update, context)
            # Payment check
            user_id = update.effective_chat.id
            auth = self.authorize(user_id)
            if auth is False:
                return
            try:
                input_msg = ''.join(context.args).split(',')
                input_msg = [x.upper() for x in input_msg]

                # Fetch already stored interest coin from db
                db_client = InitDBClient(**self.local_db_dict)
                db_client.curr.execute("""SELECT interest_coin FROM user_info WHERE user_id=%s""", user_id)
                fetched_interest_coin_str = db_client.curr.fetchall()[0]['interest_coin']

                if fetched_interest_coin_str == None:
                    temp_str = '없음'
                else:
                    temp_str = fetched_interest_coin_str

                if context.args == []:
                    body = f"등록된 관심코인을 삭제하는 명령어입니다.\n"
                    body += f"/rmint 코인심볼 형태로 입력 해 주세요.\n"
                    body += f"여러 코인을 동시에 삭제하실 수 있으며, /rmint all 입력 시 모든 코인을 삭제합니다.\n"
                    body += f"ex1) /rmint btc,eth,xrp\n"
                    body += f"ex2) /rmint all\n\n"
                    body += f"<b>현재 등록된 관심코인: {temp_str}</b>"
                    self.bot.send_thread(chat_id=user_id, text=body, parse_mode=telegram.ParseMode.HTML)
                    db_client.conn.close()
                    return

                if 'ALL' in input_msg:
                    new_interest_coin_str = None
                    db_client.curr.execute("""UPDATE user_info SET interest_coin=%s WHERE user_id=%s""", (new_interest_coin_str, user_id))
                    db_client.conn.commit()
                    db_client.conn.close()
                    body = f"모든 등록된 관심코인이 삭제되었습니다.\n\n"
                    body += f"<b>현재 등록된 관심코인: 없음</b>"
                    self.bot.send_thread(chat_id=user_id, text=body, parse_mode=telegram.ParseMode.HTML)
                    return
        
                fetched_interest_coin_list = fetched_interest_coin_str.split(',')
                new_interest_coin_list = [x for x in fetched_interest_coin_list if x not in input_msg]
                if new_interest_coin_list == []:
                    new_interest_coin_str = None
                    temp_str = '없음'
                else:
                    new_interest_coin_str = ','.join(new_interest_coin_list)
                    temp_str = new_interest_coin_str
                db_client.curr.execute("""UPDATE user_info SET interest_coin=%s WHERE user_id=%s""", (new_interest_coin_str, user_id))
                db_client.conn.commit()
                db_client.conn.close()
                body = f"{','.join(input_msg)}가 관심코인에서 삭제되었습니다.\n\n"
                body += f"<b>현재 등록된 관심코인: {temp_str}</b>"
                self.bot.send_thread(chat_id=user_id, text=body, parse_mode=telegram.ParseMode.HTML)
                return
            except Exception as e:
                body = f"서비스에 불편을 드려 죄송합니다. 일시적인 오류가 발생했습니다. 관리자에게 문의 해 주세요. (@charlie1155)\n"
                body += f"error: {e}"
                self.bot.send_thread(chat_id=user_id, text=body)
                return
        rmint_thread_th = Thread(target=rmint_thread, daemon=True)
        rmint_thread_th.start()

    def addcoin(self, update, context, verbose=True, addcir_uuid=None, new=True, register_deactivate=False):
        def addcoin_thread():
            if verbose:
                self.get_log('addcoin', update, context)
            # Payment check
            user_id = update.effective_chat.id
            auth = self.authorize(user_id)
            if auth is False:
                return
            try:
                input_msg = ''.join(context.args).split(',')
                input_msg = [x.upper() for x in input_msg]
                fauto_switch = False
                pauto_switch = False
                overwrite = False

                db_client = InitDBClient(**self.local_db_dict)
                db_client.curr.execute("""SELECT * FROM addcoin WHERE user_id=%s""", user_id)
                fetched_addcoin_df = pd.DataFrame(db_client.curr.fetchall())
                fetched_addcoin_df = fetched_addcoin_df.where(fetched_addcoin_df.notnull(), None)
                db_client.conn.close()

                if 'PAUTO' in input_msg:
                    res = self.pauto_func(user_id, fetched_addcoin_df, input_msg)
                    if res == False:
                        return
                    else:
                        auto_trade_switch, pauto_switch, auto_trade_capital, buf, input_msg = res
                elif 'AUTO' in input_msg:
                    res = self.auto_func(user_id, input_msg)
                    if res == False:
                        return
                    else:
                        auto_trade_switch, auto_trade_capital, input_msg = res
                else:
                    auto_trade_switch = None
                    auto_trade_capital = None

                if auto_trade_switch is not None:
                    # api key validation
                    try:
                        user_upbit_access_key, user_upbit_secret_key = self.snatcher.user_api_key_df[(self.snatcher.user_api_key_df['user_id']==user_id)&(self.snatcher.user_api_key_df['exchange']=='UPBIT')]\
                        .sample(n=1)[['access_key', 'secret_key']].values[0]
                        user_okx_access_key, user_okx_secret_key, user_okx_passphrase = self.snatcher.user_api_key_df[(self.snatcher.user_api_key_df['user_id']==user_id)&(self.snatcher.user_api_key_df['exchange']=='OKX')]\
                        .sample(n=1)[['access_key', 'secret_key', 'passphrase']].values[0]
                    except Exception:
                        body = f"등록된 API 키가 없어 거래소와 통신이 불가능합니다.\n"
                        body += f"/api_key 명령어를 이용하여 업비트와 OKX의 API 키를 등록해 주세요."
                        self.bot.send_thread(chat_id=user_id, text=body)
                        return

                # Load fundingrate info
                tail_okx_funding_df = self.snatcher.funding_df[self.snatcher.funding_df['okx_symbol'].isin(self.get_both_listed_okx_symbols())].groupby('okx_symbol').tail(1)
                this_okx_funding_df = tail_okx_funding_df.groupby('okx_symbol')['fundingrate'].agg('mean').reset_index()
                remaining_sec = (self.snatcher.funding_df['fundingtime'].iloc[-1] - datetime.datetime.now()).seconds
                remaining_minutes = remaining_sec // 60
                hours = remaining_minutes // 60
                minutes = remaining_minutes % 60
                seconds = remaining_sec % 60
                fund_string = f'({hours}시간 {minutes}분 남음)'

                if context.args == []:
                    if self.snatcher.userinfo_df[self.snatcher.userinfo_df['user_id']==user_id]['on_off'].values[0] == 1:
                        body = f"코인심볼, 김프 Low값(%), High값(%)  을 설정하여 각 코인별 김프알림 혹은 자동거래 설정을 할 수 있습니다.\n"
                        body += f"<b>같은 코인에 대해 여러 개의 자동거래를 설정할 수 있습니다.</b>\n"
                        body += f"1. 단순알람 ex) /addcoin xrp, -1, 1\n"
                        body += f"  김프가 아닌, 테더환산 값으로 설정을 원하시는 경우 코인심볼 뒤에 USDT를 붙여서 추가하세요.\n"
                        body += f"2. 단순알람 ex) /addcoin xrpusdt, 1140, 1170\n"
                        body += f"3. <b>반자동매매</b> ex) /addcoin xrp,-1,0,auto,100000\n"
                        body += f"  파라미터 끝에 auto와 투입금액(원)을 추가 입력하시면 <b>자동매매가 활성화</b> 됩니다.\n"
                        body += f"4. <b>김프%자동매매</b> ex) /addcoin xrp,pauto,0.5,100000\n"
                        body += f"  코인심볼 뒤에 pauto와 김프폭%, 투입금액을 입력하시면 단기예측값과 입력된 김프폭%을 바탕으로 하한선과 상한선이 자동설정 됩니다.\n"
                        body += f"<b>자동매매와 기능과 관련된 자세한 설명은 /help3</b> 를 통해 확인가능하며 등록된 설정들은 <b>/rmcoin 을 이용하여 삭제</b>할 수 있습니다.\n"
                        body += f"특정 코인의 /addcoin 설정목록을 조회하고 싶으시면 /showcoin 명령어를 이용하여 조회할 수 있습니다.\n\n"
                    else:
                        body = ""
                    body += f"<b>현재 감지리스트</b>\n"
                    if len(fetched_addcoin_df) != 0:
                        reply_markup = addcoin_InlineKeyboardButton(fetched_addcoin_df, user_id)
                        # add total capital
                        waiting_for_enter_addcoin_df = fetched_addcoin_df[fetched_addcoin_df['auto_trade_switch']==0]
                        waiting_for_exit_addcoin_df = fetched_addcoin_df[fetched_addcoin_df['auto_trade_switch']==-1]
                        if len(waiting_for_enter_addcoin_df) != 0:
                            body += f"진입대기 중인 금액: {krw(int(waiting_for_enter_addcoin_df['auto_trade_capital'].sum()))}원\n"                        
                        if len(waiting_for_exit_addcoin_df) != 0:
                            body += f"탈출대기 중인 금액: {krw(int(waiting_for_exit_addcoin_df['auto_trade_capital'].sum()))}원\n"                        
                        if len(waiting_for_enter_addcoin_df) != 0 or len(waiting_for_exit_addcoin_df) != 0:
                            body += f"진입대기+탈출대기: {krw(int(waiting_for_enter_addcoin_df['auto_trade_capital'].sum()+waiting_for_exit_addcoin_df['auto_trade_capital'].sum()))}원\n\n"
                    else:
                        reply_markup = None
                    body += self.show_addcoin_list(fetched_addcoin_df, this_okx_funding_df, fund_string)
                    
                    # send message
                    self.bot.send_thread_split_by_number(user_id, body, reply_markup=reply_markup)
                    return

                if len(input_msg) != 3:
                    body = f"잘못된 입력입니다. /addcoin 을 입력하여 사용법을 확인 해 주세요."
                    self.bot.send_thread(chat_id=user_id, text=body)
                    return

                input_symbol = input_msg[0].upper()
                # try to check if the input_symbol is an alarm_id
                try:
                    input_addcoin_display_id = int(input_symbol)
                    input_addcoin_redis_uuid = display_id_to_redis_uuid(user_id, self.snatcher.addcoin_df, input_addcoin_display_id)
                    not_waiting_fetched_addcoin_df = fetched_addcoin_df[fetched_addcoin_df['auto_trade_switch']!=-1]
                    if len(not_waiting_fetched_addcoin_df) == 0:
                        body = f"/addcoin 에 진입대기중 혹은 탈출완료인 거래가 존재하지 않습니다."
                        self.bot.send_thread(chat_id=user_id, text=body)
                        return
                    else:
                        not_waiting_addcoin_redis_uuid_list = not_waiting_fetched_addcoin_df['redis_uuid'].to_list()
                        if input_addcoin_redis_uuid not in not_waiting_addcoin_redis_uuid_list:
                            body = f"/addcoin 에 진입대기중 혹은 탈출완료인 거래ID:{input_addcoin_display_id}({input_addcoin_redis_uuid}) 가 조회되지 않습니다."
                            self.bot.send_thread(chat_id=user_id, text=body)
                            return
                        overwrite = True
                # just symbol
                except:
                    if input_symbol not in self.get_input_symbol_list():
                        body = f"{input_symbol}은 업비트와 OKX USDT 선물시장에 동시상장되지 않은 코인입니다."
                        self.bot.send_thread(chat_id=user_id, text=body)
                        return
                try:
                    input_high = float(input_msg[2])
                    input_low = float(input_msg[1])
                except:
                    body = f"High 값과 Low 값은 숫자만 입력 가능합니다. /addcoin 을 입력하여 사용법을 확인 해 주세요."
                    self.bot.send_thread(chat_id=user_id, text=body)
                    return
                
                if input_high <= input_low:
                    body = f"High 값은 Low 값보다 높아야 합니다."
                    self.bot.send_thread(chat_id=user_id, text=body)
                    return

                if 'USDT' in input_symbol:
                    if input_high < 500 or input_low < 500:
                        body = f"Low값: {input_low}과 High 값: {input_high}이 너무 작습니다.\n"
                        body += f"김프%로 설정하시려면 /addcoin {input_symbol} 이 아닌, /addcoin {input_symbol.replace('USDT', '')} 으로 입력하세요."
                        self.bot.send_thread(chat_id=user_id, text=body)
                        return
                else:
                    if input_high > 100 or input_low > 100:
                        body = f"Low값: {input_low}과 High 값: {input_high}이 너무 큽니다.\n"
                        body += f"USDT환산가로 설정하시려면 /addcoin {input_symbol} 이 아닌, /addcoin {input_symbol}USDT 으로 입력하세요."
                        self.bot.send_thread(chat_id=user_id, text=body)
                        return

                # Check the input krw whether it's bigger than Market max order
                if auto_trade_capital != None:
                    max_input_df = self.get_max_input_df()
                    coin_max_input_df = max_input_df[max_input_df['symbol'].str.contains(input_symbol.replace('USDT', ''))]
                    max_input_krw = coin_max_input_df['max_input_krw'].values[0]
                    if auto_trade_capital > max_input_krw:
                        body = f"설정된 투입금액 {krw(auto_trade_capital)}원이 OKX {input_symbol.replace('USDT','')+'USDT'}선물에서 허용된 시장가 주문최대금액({krw(max_input_krw)}원)을 초과하여,\n"
                        body += f"/addcoin 설정이 취소됩니다.\n"
                        body += f"투입금액을 낮추어서 다시 설정하여 주세요.\n"
                        self.bot.send_thread(chat_id=user_id, text=body)
                        # deactivate_addcoin_addcir(user_id, alarm_id, '/rmcoin  비활성화')
                        return

                # Passed all validation
                if auto_trade_switch is not None:
                    # Change Margin Type and Leverage according to the user's setting
                    # okx_cross == 0 -> Isolated, okx_cross == 1 -> Cross
                    okx_symbol = input_symbol.replace('USDT', '') + '-USDT-SWAP'
                    user_okx_cross = self.snatcher.userinfo_df[self.snatcher.userinfo_df['user_id']==user_id]['okx_cross'].values[0]
                    user_okx_leverage = self.snatcher.userinfo_df[self.snatcher.userinfo_df['user_id']==user_id]['okx_leverage'].values[0]
                    try:
                        if user_okx_cross == 0:
                            res = self.okx_adaptor.okx_change_leverage(user_okx_access_key, user_okx_secret_key, user_okx_passphrase, okx_symbol, user_okx_leverage, 'isolated')
                            if res['sCode'] == "0":
                                body = f"{okx_symbol} 마켓이 격리(Isolated)마진, 레버리지 {user_okx_cross}배로 변경되었습니다.\n"
                                body += f"{okx_symbol} USD-M 마켓 의 마진타입과 레버리지를 수동으로 변경하지 마십시오.\n"
                            else:
                                raise Exception(f"마진모드설정에서 에러가 발생했습니다. okx_cross: {user_okx_cross}, okx_leverage: {user_okx_leverage} error:{res['sMsg']}")
                        elif user_okx_cross == 1:
                            res = self.okx_adaptor.okx_change_leverage(user_okx_access_key, user_okx_secret_key, user_okx_passphrase, okx_symbol, user_okx_leverage, 'cross')
                            if res['sCode'] == "0":
                                body = f"{okx_symbol} 마켓이 교차(Cross)마진, 레버리지 {user_okx_cross}배로 변경되었습니다.\n"
                                body += f"{okx_symbol} USD-M 마켓 의 마진타입과 레버리지를 수동으로 변경하지 마십시오.\n"
                            else:
                                raise Exception(f"마진모드설정에서 에러가 발생했습니다. okx_cross: {user_okx_cross}, okx_leverage: {user_okx_leverage} error:{res['sMsg']}")
                    except:
                        self.telegram_bot_logger.error(f"addcoin|마진모드 변경에서 에러 발생. {traceback.format_exc()}")
                        raise Exception(f"마진모드설정에서 에러가 발생했습니다.")

                # UPDATE addcoin settings to the database if uuid provided by addcir (Already existing setting)
                db_client = InitDBClient(**self.local_db_dict)
                if addcir_uuid != None and new==False: # refresh
                    # Check whether it's already been entered by low_high break func
                    db_client.curr.execute("""SELECT auto_trade_switch FROM addcoin WHERE addcoin_uuid=%s""", addcir_uuid)
                    fetched_auto_trade_switch = db_client.curr.fetchall()[0]['auto_trade_switch']
                    if fetched_auto_trade_switch == -1: # If it's already been entered, do not refresh the addcoin setting.
                        body = f"alarm_id's addcoin_uuid: {addcir_uuid} has already been entered to kimp trading"
                        self.bot.send_thread(chat_id=self.admin_id, text=body)
                    else: # Refresh the addcoin setting if it's not entered.
                        db_client.curr.execute("""UPDATE addcoin SET last_updated_timestamp=%s,high=%s,low=%s,switch=%s,auto_trade_switch=%s,auto_trade_capital=%s WHERE addcoin_uuid=%s""", 
                        (datetime.datetime.now().timestamp()*10000000, 
                        input_high, 
                        input_low, 
                        1,
                        auto_trade_switch, 
                        auto_trade_capital,
                        addcir_uuid))
                # INSERT addcoin settings but deactivate it according to the addcir limit.
                # 최초 등록 시, 탈출완료로 표기하여 deactivate
                elif addcir_uuid != None and register_deactivate == True:
                    db_client.curr.execute("""INSERT INTO addcoin(last_updated_timestamp, user_id, redis_uuid, symbol, addcoin_uuid, high, low, switch, auto_trade_switch, auto_trade_capital)
                    VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""", (datetime.datetime.now().timestamp()*10000000, user_id, str(uuid.uuid4()), input_symbol, addcir_uuid, input_high, input_low, None, 1, auto_trade_capital))
                # UPDATE addcoin settings if alarm_id is provided by an user (overwrite)
                elif overwrite == True:
                    db_client.curr.execute("""UPDATE addcoin SET last_updated_timestamp=%s,high=%s,low=%s,switch=%s,auto_trade_switch=%s,auto_trade_capital=%s WHERE redis_uuid=%s""", 
                    (datetime.datetime.now().timestamp()*10000000, 
                    input_high, 
                    input_low, 
                    None,
                    auto_trade_switch, 
                    auto_trade_capital,
                    input_addcoin_redis_uuid))
                # INSERT addcoin settings to the database if uuid is None (Not existing)
                # or new==True (by addcir)
                else:
                    db_client.curr.execute("""INSERT INTO addcoin(last_updated_timestamp, user_id, redis_uuid, symbol, addcoin_uuid, high, low, switch, auto_trade_switch, auto_trade_capital)
                    VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""", (datetime.datetime.now().timestamp()*10000000, user_id, str(uuid.uuid4()), input_symbol, addcir_uuid, input_high, input_low, None, auto_trade_switch, auto_trade_capital))
                db_client.conn.commit()
                # fetch stored records
                db_client.curr.execute("""SELECT * FROM addcoin WHERE user_id=%s""", user_id)
                fetched_addcoin_df = pd.DataFrame(db_client.curr.fetchall())
                fetched_addcoin_df = fetched_addcoin_df.where(fetched_addcoin_df.notnull(), None)
                db_client.conn.close()
                if 'USDT' in input_symbol:
                    temp_str = '원'
                    temp_str2 = '(테더환산)'
                else:
                    temp_str = '%'
                    temp_str2 = ''
                if auto_trade_switch != None:
                    temp_str3 = '진입대기중'
                    temp_str4 = f"{krw(round(int(auto_trade_capital)))}원 "
                else:
                    temp_str3 = '꺼짐'
                    temp_str4 = ''
                if overwrite == False:
                    temp_str5 = "가 정상적으로 추가되었습니다."
                else:
                    temp_str5 = "으로 정상적으로 변경되었습니다."
                body = f"코인: {input_symbol}{temp_str2}, Low: {input_low}{temp_str}, High: {input_high}{temp_str}\n 자동매매: {temp_str4}{temp_str3} {temp_str5}\n\n"
                body += "<b>현재 감지리스트</b>\n"
                # add total capital
                waiting_for_enter_addcoin_df = fetched_addcoin_df[fetched_addcoin_df['auto_trade_switch']==0]
                waiting_for_exit_addcoin_df = fetched_addcoin_df[fetched_addcoin_df['auto_trade_switch']==-1]
                if len(waiting_for_enter_addcoin_df) != 0:
                    body += f"진입대기 중인 금액: {krw(int(waiting_for_enter_addcoin_df['auto_trade_capital'].sum()))}원\n"                        
                if len(waiting_for_exit_addcoin_df) != 0:
                    body += f"탈출대기 중인 금액: {krw(int(waiting_for_exit_addcoin_df['auto_trade_capital'].sum()))}원\n"                        
                if len(waiting_for_enter_addcoin_df) != 0 or len(waiting_for_exit_addcoin_df) != 0:
                    body += f"진입대기+탈출대기: {krw(int(waiting_for_enter_addcoin_df['auto_trade_capital'].sum()+waiting_for_exit_addcoin_df['auto_trade_capital'].sum()))}원\n\n"
                body += self.show_addcoin_list(fetched_addcoin_df, this_okx_funding_df, fund_string)
                if verbose == True:
                    # send message
                    self.bot.send_thread_split_by_number(user_id, body)
                if (fauto_switch == True or pauto_switch == True) and verbose==True and new==True:
                    buf.seek(0)
                    self.bot.send_photo(chat_id=user_id, photo=buf)
                    buf.close()
                return
            except Exception as e:
                self.telegram_bot_logger.error(f"addcoin|{traceback.format_exc()}")
                body = f"서비스에 불편을 드려 죄송합니다. 일시적인 오류가 발생했습니다. 관리자에게 문의 해 주세요. (@charlie1155)\n"
                body += f"error: {e}"
                self.bot.send_thread(chat_id=user_id, text=body)
                return
        addcoin_thread_th = Thread(target=addcoin_thread, daemon=True)
        addcoin_thread_th.start()
    
    def rmcoin(self, update, context, addcir=False):
        def rmcoin_thread():
            self.get_log('rmcoin', update, context)
            # Payment check
            user_id = update.effective_chat.id
            auth = self.authorize(user_id)
            if auth is False:
                return
            try:
                input_msg = ''.join(context.args).split(',')
                input_msg = [x.upper() for x in input_msg]

                # Load fundingrate info
                tail_okx_funding_df = self.snatcher.funding_df[self.snatcher.funding_df['okx_symbol'].isin(self.get_both_listed_okx_symbols())].groupby('okx_symbol').tail(1)
                this_okx_funding_df = tail_okx_funding_df.groupby('okx_symbol')['fundingrate'].agg('mean').reset_index()
                remaining_sec = (self.snatcher.funding_df['fundingtime'].iloc[-1] - datetime.datetime.now()).seconds
                remaining_minutes = remaining_sec // 60
                hours = remaining_minutes // 60
                minutes = remaining_minutes % 60
                seconds = remaining_sec % 60
                fund_string = f'({hours}시간 {minutes}분 남음)'

                db_client = InitDBClient(**self.local_db_dict)
                db_client.curr.execute("""SELECT * FROM addcoin WHERE user_id=%s""", user_id)
                fetched_addcoin_df = pd.DataFrame(db_client.curr.fetchall())
                fetched_addcoin_df = fetched_addcoin_df.where(fetched_addcoin_df.notnull(), None)
                db_client.conn.close()

                if context.args == []:
                    body = f"등록된 코인알람설정을 삭제하는 명령어 입니다.\n"
                    body += f"하단의 버튼 클릭 혹은 /rmcoin 거래ID(/addcoin 에서 확인가능) 을 이용하여 삭제하실 수 있으며, 콤마를 사용하여 동시에 여러코인설정을 삭제하실 수 있습니다.\n"
                    body += f"ex1) /rmcoin 123\n"
                    body += f"ex2) /rmcoin 123,234,345\n"
                    body += f"/rmcoin fall 입력 시, /addcoin 에서 <b>탈출완료상태인 코인설정들</b>이 삭제됩니다. 기타 설정은 그대로 유지됩니다.\n"
                    body += f"ex3) /rmcoin fall\n"
                    body += f"/rmcoin all 입력 시, /addcoin 에서 <b>탈출대기중을 제외한 등록된 모든 코인설정들</b>이 삭제됩니다.\n"
                    body += f"ex4) /rmcoin all\n\n"
                    body += f"<b>현재 감지리스트</b>\n"
                    if len(fetched_addcoin_df) != 0:
                        reply_markup = rmcoin_InlineKeyboardButton(fetched_addcoin_df, user_id)
                        # add total capital
                        waiting_for_enter_addcoin_df = fetched_addcoin_df[fetched_addcoin_df['auto_trade_switch']==0]
                        waiting_for_exit_addcoin_df = fetched_addcoin_df[fetched_addcoin_df['auto_trade_switch']==-1]
                        if len(waiting_for_enter_addcoin_df) != 0:
                            body += f"진입 대기 중인 금액: {krw(int(waiting_for_enter_addcoin_df['auto_trade_capital'].sum()))}원\n"                        
                        if len(waiting_for_exit_addcoin_df) != 0:
                            body += f"탈출 대기 중인 금액: {krw(int(waiting_for_exit_addcoin_df['auto_trade_capital'].sum()))}원\n"                        
                        if len(waiting_for_enter_addcoin_df) != 0 or len(waiting_for_exit_addcoin_df) != 0:
                            body += f"진입 대기+탈출 대기: {krw(int(waiting_for_enter_addcoin_df['auto_trade_capital'].sum()+waiting_for_exit_addcoin_df['auto_trade_capital'].sum()))}원\n\n"
                    else:
                        reply_markup = None
                    body += self.show_addcoin_list(fetched_addcoin_df, this_okx_funding_df, fund_string)
                    
                    # send message
                    self.bot.send_thread_split_by_number(user_id, body, reply_markup=reply_markup)
                    return

                if 'FALL' in input_msg:
                    db_client = InitDBClient(**self.local_db_dict)
                    db_client.curr.execute("""SELECT * FROM addcoin WHERE user_id=%s AND auto_trade_switch=%s""", (user_id,1))
                    finished_user_addcoin_df = pd.DataFrame(db_client.curr.fetchall())
                    if len(finished_user_addcoin_df) == 0:
                        db_client.conn.close()
                        body = f"탈출완료인 /addcoin 설정이 없습니다."
                        self.bot.send_thread(chat_id=user_id, text=body)
                        return
                    else:
                        finished_redis_uuid_list = finished_user_addcoin_df['redis_uuid'].to_list()
                    # Delete addcoin settings
                    db_client.curr.execute("""DELETE FROM addcoin WHERE user_id=%s AND auto_trade_switch=%s""", (user_id,1))
                    db_client.conn.commit()
                    # Display current /addcoin settings
                    body = f"탈출완료인 모든 코인 설정이 삭제되었습니다.\n\n"
                    body += f"<b>현재 감지리스트</b>\n"
                    db_client.curr.execute("""SELECT * FROM addcoin WHERE user_id=%s""", user_id)
                    fetched_addcoin_df = pd.DataFrame(db_client.curr.fetchall())
                    fetched_addcoin_df = fetched_addcoin_df.where(fetched_addcoin_df.notnull(), None)
                    db_client.conn.close()
                    if len(fetched_addcoin_df) != 0:
                        # add total capital
                        waiting_for_enter_addcoin_df = fetched_addcoin_df[fetched_addcoin_df['auto_trade_switch']==0]
                        waiting_for_exit_addcoin_df = fetched_addcoin_df[fetched_addcoin_df['auto_trade_switch']==-1]
                        if len(waiting_for_enter_addcoin_df) != 0:
                            body += f"진입 대기 중인 금액: {krw(int(waiting_for_enter_addcoin_df['auto_trade_capital'].sum()))}원\n"                        
                        if len(waiting_for_exit_addcoin_df) != 0:
                            body += f"탈출 대기 중인 금액: {krw(int(waiting_for_exit_addcoin_df['auto_trade_capital'].sum()))}원\n"                        
                        if len(waiting_for_enter_addcoin_df) != 0 or len(waiting_for_exit_addcoin_df) != 0:
                            body += f"진입 대기+탈출 대기: {krw(int(waiting_for_enter_addcoin_df['auto_trade_capital'].sum()+waiting_for_exit_addcoin_df['auto_trade_capital'].sum()))}원\n\n"
                    body += self.show_addcoin_list(fetched_addcoin_df, this_okx_funding_df, fund_string)

                    # send message
                    self.bot.send_thread_split_by_number(user_id, body)
                    return

                if 'ALL' in input_msg:
                    db_client = InitDBClient(**self.local_db_dict)
                    db_client.curr.execute("""SELECT * FROM addcoin WHERE user_id=%s AND (auto_trade_switch!=%s OR auto_trade_switch IS NULL)""", (user_id,-1))
                    not_waiting_user_addcoin_df = pd.DataFrame(db_client.curr.fetchall())
                    if len(not_waiting_user_addcoin_df) == 0:
                        not_waiting_redis_uuid_list = []
                    else:
                        not_waiting_redis_uuid_list = not_waiting_user_addcoin_df['redis_uuid'].to_list()
                    # Deactivate addcir settings
                    if addcir == False:
                        for each_redis_uuid in not_waiting_redis_uuid_list:
                            self.deactivate_addcoin_addcir(user_id, each_redis_uuid, '/rmcoin 삭제로 인한 비활성화')
                    # Delete addcoin settings
                    db_client.curr.execute("""DELETE FROM addcoin WHERE user_id=%s AND (auto_trade_switch!=%s OR auto_trade_switch IS NULL)""", (user_id,-1))
                    db_client.conn.commit()
                    # Display current /addcoin settings
                    body = f"탈출대기중을 제외한 모든 코인 알람이 삭제되었습니다.\n\n"
                    body += f"<b>현재 감지리스트</b>\n"
                    db_client.curr.execute("""SELECT * FROM addcoin WHERE user_id=%s""", user_id)
                    fetched_addcoin_df = pd.DataFrame(db_client.curr.fetchall())
                    fetched_addcoin_df = fetched_addcoin_df.where(fetched_addcoin_df.notnull(), None)
                    db_client.conn.close()
                    body += self.show_addcoin_list(fetched_addcoin_df, this_okx_funding_df, fund_string)
                    # send message
                    self.bot.send_thread_split_by_number(user_id, body)
                    return

                db_client = InitDBClient(**self.local_db_dict)
                for addcoin_display_id in input_msg:
                    try:
                        addcoin_display_id = int(addcoin_display_id)
                    except:
                        body = f"삭제는 코인이름이 아닌, 거래ID 를 입력해 주셔야 합니다.\n"
                        body += f"/rmcoin 을 입력하여 사용법을 확인 해 주세요."
                        self.bot.send_thread(chat_id=user_id, text=body)
                        db_client.conn.close()
                        return
                    if addcoin_display_id <= 0:
                        body = f"거래ID 는 1 이상의 숫자만 입력이 가능합니다.\n"
                        body += f"/rmcoin 을 입력하여 사용법을 확인 해 주세요."
                        self.bot.send_thread(chat_id=user_id, text=body)
                        db_client.conn.close()
                        return
                    input_redis_uuid = display_id_to_redis_uuid(user_id, self.snatcher.addcoin_df, addcoin_display_id)
                    res = db_client.curr.execute("""SELECT * FROM addcoin WHERE redis_uuid=%s and user_id=%s""", (input_redis_uuid, user_id))
                    if res == 0:
                        body = f"거래ID: {addcoin_display_id} 는 /addcoin 에 등록되어 있지 않습니다."
                        body += f"/rmcoin 을 입력하여 사용법을 확인 해 주세요."
                        self.bot.send_thread(chat_id=user_id, text=body)
                        db_client.conn.close()
                        return
                    db_client.curr.execute("""DELETE FROM addcoin WHERE redis_uuid=%s and user_id=%s""", (input_redis_uuid, user_id))
                    if addcir == False:
                        self.deactivate_addcoin_addcir(user_id, input_redis_uuid, '/rmcoin 삭제로 인한 비활성화')
                db_client.conn.commit()
                body = f"거래ID: {','.join(input_msg)}의 /addcoin 설정이 삭제되었습니다.\n\n"
                body += f"<b>현재 감지리스트</b>\n"
                db_client.curr.execute("""SELECT * FROM addcoin WHERE user_id=%s""", user_id)
                fetched_addcoin_df = pd.DataFrame(db_client.curr.fetchall())
                fetched_addcoin_df = fetched_addcoin_df.where(fetched_addcoin_df.notnull(), None)
                db_client.conn.close()
                if len(fetched_addcoin_df) != 0:
                    reply_markup = rmcoin_InlineKeyboardButton(fetched_addcoin_df, user_id)
                    # add total capital
                    waiting_for_enter_addcoin_df = fetched_addcoin_df[fetched_addcoin_df['auto_trade_switch']==0]
                    waiting_for_exit_addcoin_df = fetched_addcoin_df[fetched_addcoin_df['auto_trade_switch']==-1]
                    if len(waiting_for_enter_addcoin_df) != 0:
                        body += f"진입 대기 중인 금액: {krw(int(waiting_for_enter_addcoin_df['auto_trade_capital'].sum()))}원\n"                        
                    if len(waiting_for_exit_addcoin_df) != 0:
                        body += f"탈출 대기 중인 금액: {krw(int(waiting_for_exit_addcoin_df['auto_trade_capital'].sum()))}원\n"                        
                    if len(waiting_for_enter_addcoin_df) != 0 or len(waiting_for_exit_addcoin_df) != 0:
                        body += f"진입 대기+탈출 대기: {krw(int(waiting_for_enter_addcoin_df['auto_trade_capital'].sum()+waiting_for_exit_addcoin_df['auto_trade_capital'].sum()))}원\n\n"
                    body += self.show_addcoin_list(fetched_addcoin_df, this_okx_funding_df, fund_string)
                else:
                    reply_markup = None
                # send message
                self.bot.send_thread_split_by_number(user_id, body, reply_markup=reply_markup)
                return
            except Exception as e:
                self.telegram_bot_logger.error(f"rmcoin|{traceback.format_exc()}")
                body = f"서비스에 불편을 드려 죄송합니다. 일시적인 오류가 발생했습니다. 관리자에게 문의 해 주세요. (@charlie1155)\n"
                body += f"error: {e}"
                self.bot.send_thread(chat_id=user_id, text=body)
                return
        rmcoin_thread_th = Thread(target=rmcoin_thread, daemon=True)
        rmcoin_thread_th.start()
    
    def showcoin(self, update, context):
        def showcoin_thread():
            self.get_log('showcoin', update, context)
            # Payment check
            user_id = update.effective_chat.id
            auth = self.authorize(user_id)
            if auth is False:
                return
            try:
                if context.args == []:
                    body = f"/showcoin 명령어를 이용하여 /addcoin 에 등록된 자동거래 중 원하는 코인의 거래들만 조회할 수 있습니다.\n"
                    body += f"코인심볼 입력 시, 김프거래 뿐만 아니라, <b>테더환산가로 등록된 자동거래도 같이 조회</b>됩니다.\n"
                    body += f"ex) /showcoin btc"
                    self.bot.send_thread(chat_id=user_id, text=body, parse_mode=telegram.ParseMode.HTML)
                    return

                input_msg = ''.join(context.args).split(',')
                input_msg = [x.upper() for x in input_msg]

                if len(input_msg) != 1:
                    body = f"코인심볼은 하나만 입력 해 주세요."
                    self.bot.send_thread(chat_id=user_id, text=body)
                    return
                
                if input_msg[0].replace('USDT', '') not in [x.replace('-USDT-SWAP', '') for x in self.get_both_listed_okx_symbols()]:
                    body = f"{input_msg[0].replace('USDT', '')}은 업비트와 OKX USD-M 선물시장에 동시상장된 코인이 아닙니다."
                    self.bot.send_thread(chat_id=user_id, text=body)
                    return
                
                # Passed validation
                input_symbol = input_msg[0].replace('USDT', '')
                db_client = InitDBClient(**self.local_db_dict)
                db_client.curr.execute("""SELECT * FROM addcoin WHERE user_id=%s""", user_id)
                fetched_addcoin_df = pd.DataFrame(db_client.curr.fetchall())
                fetched_addcoin_df = fetched_addcoin_df.where(fetched_addcoin_df.notnull(), None)
                db_client.conn.close()
                if len(fetched_addcoin_df) == 0:
                    body = f"등록된 /addcoin 설정이 존재하지 않습니다."
                    self.bot.send_thread(chat_id=user_id, text=body)
                    return
                filtered_fetched_addcoin_df = fetched_addcoin_df[fetched_addcoin_df['symbol'].str.contains(input_symbol)].reset_index(drop=True)
                if len(filtered_fetched_addcoin_df) == 0:
                    body = f"등록된 {input_symbol} /addcoin 설정이 존재하지 않습니다."
                    self.bot.send_thread(chat_id=user_id, text=body)
                    return

                # Load fundingrate info
                tail_okx_funding_df = self.snatcher.funding_df[self.snatcher.funding_df['okx_symbol'].isin(self.get_both_listed_okx_symbols())].groupby('okx_symbol').tail(1)
                this_okx_funding_df = tail_okx_funding_df.groupby('okx_symbol')['fundingrate'].agg('mean').reset_index()
                remaining_sec = (self.snatcher.funding_df['fundingtime'].iloc[-1] - datetime.datetime.now()).seconds
                remaining_minutes = remaining_sec // 60
                hours = remaining_minutes // 60
                minutes = remaining_minutes % 60
                seconds = remaining_sec % 60
                fund_string = f'({hours}시간 {minutes}분 남음)'

                body = f"<b>현재 감지리스트 ({input_symbol})</b>\n"
                if len(filtered_fetched_addcoin_df) != 0:
                    # add total capital
                    waiting_for_enter_addcoin_df = filtered_fetched_addcoin_df[filtered_fetched_addcoin_df['auto_trade_switch']==0]
                    waiting_for_exit_addcoin_df = filtered_fetched_addcoin_df[filtered_fetched_addcoin_df['auto_trade_switch']==-1]
                    if len(waiting_for_enter_addcoin_df) != 0:
                        body += f"진입대기 중인 금액: {krw(int(waiting_for_enter_addcoin_df['auto_trade_capital'].sum()))}원\n"                        
                    if len(waiting_for_exit_addcoin_df) != 0:
                        body += f"탈출대기 중인 금액: {krw(int(waiting_for_exit_addcoin_df['auto_trade_capital'].sum()))}원\n"                        
                    if len(waiting_for_enter_addcoin_df) != 0 or len(waiting_for_exit_addcoin_df) != 0:
                        body += f"진입대기+탈출대기: {krw(int(waiting_for_enter_addcoin_df['auto_trade_capital'].sum()+waiting_for_exit_addcoin_df['auto_trade_capital'].sum()))}원\n\n"
                body += self.show_addcoin_list(filtered_fetched_addcoin_df, this_okx_funding_df, fund_string)
                # send message
                self.bot.send_thread_split_by_number(user_id, body)
                return
            except Exception as e:
                self.telegram_bot_logger.error(f"showcoin|{traceback.format_exc()}")
                body = f"서비스에 불편을 드려 죄송합니다. 일시적인 오류가 발생했습니다. 관리자에게 문의 해 주세요. (@charlie1155)\n"
                body += f"error: {e}"
                self.bot.send_thread(chat_id=user_id, text=body)
                return
        showcoin_thread_th = Thread(target=showcoin_thread, daemon=True)
        showcoin_thread_th.start()

    def addcir(self, update, context):
        def addcir_thread():
            self.get_log('addcir', update, context)
            user_id = update.effective_chat.id
            # Payment check
            auth = self.authorize(user_id)
            if auth is False:
                return
            try:
                try:
                    user_upbit_access_key, user_upbit_secret_key = self.snatcher.user_api_key_df[(self.snatcher.user_api_key_df['user_id']==user_id)&(self.snatcher.user_api_key_df['exchange']=='UPBIT')]\
                    .sample(n=1)[['access_key', 'secret_key']].values[0]
                    user_okx_access_key, user_okx_secret_key, user_okx_passphrase = self.snatcher.user_api_key_df[(self.snatcher.user_api_key_df['user_id']==user_id)&(self.snatcher.user_api_key_df['exchange']=='OKX')]\
                    .sample(n=1)[['access_key', 'secret_key', 'passphrase']].values[0]
                except Exception:
                    body = f"등록된 API 키가 없어 거래소와 통신이 불가능합니다.\n"
                    body += f"/api_key 명령어를 이용하여 업비트와 OKX의 API 키를 등록해 주세요."
                    self.bot.send_thread(chat_id=user_id, text=body)
                    return

                input_msg = ''.join(context.args).split(',')
                input_msg = [x.upper() for x in input_msg]
                overwrite = False

                db_client = InitDBClient(**self.local_db_dict)
                db_client.curr.execute("""SELECT * FROM addcir WHERE user_id=%s""", user_id)
                addcir_df = pd.DataFrame(db_client.curr.fetchall()).reset_index(drop=True)
                addcir_df = addcir_df.where(addcir_df.notnull(), None)
                db_client.conn.close()

                if context.args == []:
                    if self.snatcher.userinfo_df[self.snatcher.userinfo_df['user_id']==user_id]['on_off'].values[0] == 1:
                        body = f"/addcir 명령어로 김프진입과 탈출을 자동으로 반복할 코인을 등록할 수 있으며,\n"
                        body += f"같은 코인에 대해서도 여러 개의 addcir 설정을 하실 수 있습니다.(각 설정 별 개별적으로 작동)\n"
                        body += f"/rmcir 명령어로 등록된 설정을 삭제할 수 있습니다.\n"
                        body += f"/addcirl 명령어로 특정 김프 이상에서 /addcir 를 임시 비활성화 하여 /addcoin 의 자동재등록을 제한할 수 있으며,\n"
                        body += f"/addcirn 명령어로 /addcir 로 발동되는 /addcoin 탈출 시 자동 재진입 최대 횟수를 설정가능 합니다.\n"
                        body += f"/addcoin 의 설정법과 동일한 문법과 방법으로 특정코인에 대한 반복거래를 설정할 수 있으며,\n"
                        body += f"/addcir 에서도 코인심볼 대신 존재하는 반복ID 를 입력하시면 설정 덮어쓰기가 가능합니다.\n"
                        body += f"ex1) /addcir xrp, 1, 2, auto, 1000000(운용금액)\n"
                        body += f"ex2) /addcir xrp, pauto, 0.5, 1000000\n\n"
                        body += f"/addcir 이 설정되면, /addcoin 의 거래기능들을 활용하게 되며, 김프추세를 추적하기 위해, 김프거래에 진입이 될 때까지 매 3분 마다 추세를 새로 계산하여 /addcoin 의 low와 high가 갱신됩니다.(fauto, pauto 경우에 해당)\n"
                        body += f"/addcoin 이 작동하여 김프거래가 진입된 이후에는, 해당 거래가 탈출될 때까지 모니터링 하며, 김프거래 탈출 즉시 자동으로 /addcir 설정에 따라 /addcoin 이 재등록 됩니다.\n"
                        body += f"기타 자동거래에 대한 자세한 설명은 /help3 를 입력하여 확인 해 주세요.\n"
                        # body += f"김프거래를 반복하는 과정에서, 한 쪽의 거래소잔고가 부족해지는 경우,\n"
                        # body += f"잔고가 부족한 거래소의 잔고에 맞추어 진입금액이 자동조정됩니다.\n"
                        # body += f"만약, 한 쪽 거래소잔고가 최초잔고의 50% 이하가 되는 경우, 자동반복거래가 중지됩니다.\n"
                        body += f"특정 코인의 /addcir 설정목록을 조회하고 싶으시면 /showcir 명령어를 이용하여 조회할 수 있습니다.\n\n\n"
                    else:
                        body = ""

                    # Load currently registered addcir_df df
                    body += f"<b>현재 등록된 반복거래</b>"
                    body += self.show_addcir_list(addcir_df)
                    # send message
                    self.bot.send_thread_split_by_number(user_id, body)
                    return

                # Common validation process
                if len(input_msg) != 4 and len(input_msg) != 5:
                    body = f"잘못된 입력입니다. /addcir 을 입력하여 사용법을 확인 해 주세요."
                    self.bot.send_thread(chat_id=user_id, text=body)
                    return
                if 'AUTO' not in input_msg and 'PAUTO' not in input_msg and 'FAUTO' not in input_msg:
                    body = f"잘못된 입력입니다. /addcir 을 입력하여 사용법을 확인 해 주세요."
                    self.bot.send_thread(chat_id=user_id, text=body)
                    return
                input_symbol = input_msg[0].upper()
                # try to check if the input_symbol is a circle_id
                try:
                    input_addcir_display_id = int(input_symbol)
                    input_addcir_redis_uuid = display_id_to_redis_uuid(user_id, addcir_df, input_addcir_display_id)
                    user_addcir_df = addcir_df[addcir_df['user_id']==user_id]
                    if len(user_addcir_df) == 0:
                        body = f"/addcir 에 등록된 반복거래가 없습니다."
                        self.bot.send_thread(chat_id=user_id, text=body)
                        return
                    else:
                        user_addcir_redis_uuid_list = user_addcir_df['redis_uuid'].to_list()
                        if input_addcir_redis_uuid not in user_addcir_redis_uuid_list:
                            body = f"반복ID가 {input_addcir_display_id}인 /addcir 설정이 조회되지 않습니다."
                            self.bot.send_thread(chat_id=user_id, text=body)
                            return
                        overwrite = True
                        current_addcir_uuid = addcir_df[addcir_df['redis_uuid']==input_addcir_redis_uuid]['addcir_uuid'].values[0]
                        current_symbol = addcir_df[addcir_df['redis_uuid']==input_addcir_redis_uuid]['symbol'].values[0]
                # just symbol
                except:
                    if input_symbol not in self.get_input_symbol_list():
                        body = f"{input_symbol}은 업비트와 OKX USDT 선물시장에 동시상장되지 않은 코인입니다."
                        self.bot.send_thread(chat_id=user_id, text=body)
                        return
                try:
                    input_capital = int(input_msg[-1])
                except:
                    body = f"운용금액은 양수의 숫자만 입력이 가능합니다."
                    self.bot.send_thread(chat_id=user_id, text=body)
                    return
                if input_capital <= 5*self.get_dollar_dict()['price']:
                    body = f"운용금액은 {5*self.get_dollar_dict()['price']:}원(5USDT) 이상부터 설정가능합니다."
                    self.bot.send_thread(chat_id=user_id, text=body)
                    return
                # Check the input krw whether it's bigger than Market max order
                max_input_df = self.get_max_input_df()
                coin_max_input_df = max_input_df[max_input_df['symbol'].str.contains(input_symbol.replace('USDT', ''))]
                max_input_krw = coin_max_input_df['max_input_krw'].values[0]
                if input_capital > max_input_krw:
                    body = f"설정된 운용금액 {krw(input_capital)}원이 OKX {input_symbol.replace('USDT','')+'USDT'}선물에서 허용된 시장가 주문최대금액({krw(max_input_krw)}원)을 초과하여,\n"
                    body += f"/addcoin 설정이 취소됩니다.\n"
                    body += f"투입금액을 낮추어서 다시 설정하여 주세요.\n"
                    self.bot.send_thread(chat_id=user_id, text=body)
                    # deactivate_addcoin_addcir(user_id, alarm_id, '/rmcoin  비활성화')
                    return

                # When it's using auto feature of /addcoin
                if 'AUTO' in input_msg:
                    trade_type = 1
                    input_pauto_num = None
                    input_fauto_num = None
                    try:
                        input_auto_low = float(input_msg[1])
                        input_auto_high = float(input_msg[2])
                    except:
                        body = f"Low 값과 High 값은 숫자만 입력가능합니다."
                        self.bot.send_thread(chat_id=user_id, text=body)
                        return
                    if input_auto_low >= input_auto_high:
                        body = f"Low 값이 High 값보다 같거나 클 수 없습니다."
                        self.bot.send_thread(chat_id=user_id, text=body)
                        return
                    if overwrite == False:
                        if 'USDT' in input_symbol:
                            if input_auto_high < 500 or input_auto_low < 500:
                                body = f"Low값: {input_auto_low} 혹은 High 값: {input_auto_high}이 너무 작습니다.\n"
                                body += f"김프%로 설정하시려면 코인심볼을 {input_symbol} 이 아닌, {input_symbol.replace('USDT', '')} 으로 설정하세요."
                                self.bot.send_thread(chat_id=user_id, text=body)
                                return
                        else:
                            if input_auto_high > 100 or input_auto_low > 100:
                                body = f"Low값: {input_auto_low} 혹은 High 값: {input_auto_high}이 너무 큽니다.\n"
                                body += f"USDT환산가로 설정하시려면 코인심볼을 {input_symbol} 이 아닌, {input_symbol}USDT 으로 설정하세요."
                                self.bot.send_thread(chat_id=user_id, text=body)
                                return
                    else:
                        if 'USDT' in current_symbol:
                            if input_auto_high < 500 or input_auto_low < 500:
                                body = f"Low값: {input_auto_low} 혹은 High 값: {input_auto_high}이 너무 작습니다.\n"
                                body += f"김프%로 설정하시려면 코인심볼을 {current_symbol} 이 아닌, {current_symbol.replace('USDT', '')} 으로 설정하세요."
                                self.bot.send_thread(chat_id=user_id, text=body)
                                return
                        else:
                            if input_auto_high > 100 or input_auto_low > 100:
                                body = f"Low값: {input_auto_low} 혹은 High 값: {input_auto_high}이 너무 큽니다.\n"
                                body += f"USDT환산가로 설정하시려면 코인심볼을 {current_symbol} 이 아닌, {current_symbol}USDT 으로 설정하세요."
                                self.bot.send_thread(chat_id=user_id, text=body)
                                return

                # When it's using pauto feature of /addcoin
                elif 'PAUTO' in input_msg:
                    trade_type = 2
                    input_auto_low = None
                    input_auto_high = None
                    input_fauto_num = None
                    try:
                        input_pauto_num = float(input_msg[2])
                    except:
                        body = f"김프폭% 는 양수의 숫자만 입력이 가능합니다."
                        self.bot.send_thread(chat_id=user_id, text=body)
                        return
                    if input_pauto_num <= 0:
                        body = f"김프폭% 는 양수의 숫자만 입력이 가능합니다."
                        self.bot.send_thread(chat_id=user_id, text=body)
                        return

                # Passed all validation
                # Check whether there's already registered one
                addcir_uuid = uuid.uuid1().hex
                # INSERT addcir into the database
                db_client = InitDBClient(**self.local_db_dict)
                if overwrite == False:
                    sql = """INSERT INTO addcir 
                    (
                        user_id,
                        last_updated_timestamp,
                        redis_uuid,
                        symbol,
                        addcir_uuid,
                        auto_low,
                        auto_high,
                        pauto_num,
                        fauto_num, 
                        cir_trade_switch, 
                        cir_trade_capital, 
                        cir_trade_num
                        ) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
                    now_timestamp = datetime.datetime.now().timestamp()*10000000
                    val = (user_id, now_timestamp, str(uuid.uuid4()), input_symbol, addcir_uuid, input_auto_low, input_auto_high, input_pauto_num, input_fauto_num, 1, input_capital, 0)
                    db_client.curr.execute(sql, val)
                    db_client.conn.commit()
                # UPDATE addcir settins if it's overwriting
                else:
                    sql = """UPDATE addcir SET
                    last_updated_timestamp=%s
                    auto_low=%s,
                    auto_high=%s, 
                    pauto_num=%s,
                    fauto_num=%s,
                    cir_trade_switch=%s, 
                    cir_trade_capital=%s,
                    remark=%s
                    WHERE redis_uuid=%s"""
                    now_timestamp = datetime.datetime.now().timestamp()*10000000
                    val = (now_timestamp, input_auto_low, input_auto_high, input_pauto_num, input_fauto_num, 1, input_capital, None, input_addcir_redis_uuid)
                    db_client.curr.execute(sql, val)
                    db_client.conn.commit()
                db_client.conn.close()

                # Execute addcoin according to the circle coin settings
                if overwrite == False:
                    exist_flag = self.addcir_addcoin_init(trade_type, user_id, input_symbol, addcir_uuid, input_auto_low, input_auto_high, input_pauto_num, input_fauto_num, input_capital)
                    body = f"/addcir 설정으로 인해, /addcoin 에 {input_symbol}의 김프거래가 등록되었습니다.\n"
                    body += f"/addcir 에 {input_symbol}의 반복거래가 정상적으로 등록되었습니다.\n\n"
                else:
                    # if there no addcoin id that has the same uuid as the addcir, then regiter new addcoin
                    db_client = InitDBClient(**self.local_db_dict)
                    res = db_client.curr.execute("""SELECT * FROM addcoin WHERE user_id=%s""", user_id)
                    user_addcoin_df = pd.DataFrame(db_client.curr.fetchall())
                    db_client.conn.close()
                    body = ''
                    if res == 0 or len(user_addcoin_df[user_addcoin_df['addcoin_uuid']==current_addcir_uuid]) == 0:
                        self.addcir_addcoin_init(trade_type, user_id, current_symbol, current_addcir_uuid, input_auto_low, input_auto_high, input_pauto_num, input_fauto_num, input_capital)
                        body += f"/addcir 설정으로 인해, /addcoin 에 반복ID:{input_symbol}({current_symbol})의 김프거래가 등록되었습니다.\n"
                    body += f"/addcir 의 반복ID:{input_addcir_display_id}({current_symbol})의 반복거래가 정상적으로 변경 및 활성화 되었습니다.\n\n"

                # Load currently registered addcir df
                body += f"<b>현재 등록된 반복거래</b>"
                db_client = InitDBClient(**self.local_db_dict)
                db_client.curr.execute("""SELECT * FROM addcir WHERE user_id=%s""", user_id)
                addcir_df = pd.DataFrame(db_client.curr.fetchall()).reset_index(drop=True)
                addcir_df = addcir_df.where(addcir_df.notnull(), None)
                time.sleep(0.5) # Waiting for addcir_addcon_register to be done.. addcoin is going to be run as a thread..
                db_client.curr.execute("""SELECT * FROM addcoin WHERE user_id=%s""", user_id)
                addcoin_df = pd.DataFrame(db_client.curr.fetchall()).reset_index(drop=True)
                addcoin_df = addcoin_df.where(addcoin_df.notnull(), None)
                db_client.conn.close()
                body += self.show_addcir_list(addcir_df, fetched_addcoin_df=addcoin_df)
                # send message
                self.bot.send_thread_split_by_number(user_id, body)
                return
            except Exception as e:
                self.telegram_bot_logger.error(f"addcir|{traceback.format_exc()}")
                body = f"서비스에 불편을 드려 죄송합니다. 일시적인 오류가 발생했습니다. 관리자에게 문의 해 주세요. (@charlie1155)\n"
                body += f"error: {e}"
                self.bot.send_thread(chat_id=user_id, text=body)
                return
        addcir_thread_th = Thread(target=addcir_thread, daemon=True)
        addcir_thread_th.start()
    
    def rmcir(self, update, context):
        def rmcir_thread():
            self.get_log('rmcir', update, context)
            user_id = update.effective_chat.id
            # Payment check
            auth = self.authorize(user_id)
            if auth is False:
                return
            try:
                input_msg = ''.join(context.args).split(',')
                if context.args == []:
                    # Load currently registered addcir df
                    body = f"<b>현재 등록된 반복거래</b>"
                    db_client = InitDBClient(**self.local_db_dict)
                    db_client.curr.execute("""SELECT * FROM addcir WHERE user_id=%s""", user_id)
                    user_addcir_df = pd.DataFrame(db_client.curr.fetchall()).reset_index(drop=True)
                    user_addcir_df = user_addcir_df.where(user_addcir_df.notnull(), None)
                    db_client.conn.close()
                    body += self.show_addcir_list(user_addcir_df)
                    head_body = f"하단의 버튼을 클릭 혹은 /rmcir 명령어로 등록된 반복거래 설정을 삭제할 수 있습니다.\n"
                    head_body += f"/rmcir 반복ID(/addcir 에서 확인가능) 형태로 입력 해 주세요.\n"
                    head_body += f"한 번에 여러개 입력도 가능합니다.\n"
                    head_body += f"ex) /rmcir 123,345,456\n"
                    head_body += f"/rmcir all 입력 시, 등록된 모든 반복거래 설정을 삭제합니다.\n\n"
                    head_body += body
                    if len(user_addcir_df) != 0:
                        reply_markup = rmcir_InlineKeyboardButton(user_addcir_df, user_id)
                    else:
                        reply_markup = None
                    # send message
                    self.bot.send_thread_split_by_number(user_id, head_body, reply_markup=reply_markup)
                    return
                
                if 'all' in [x.lower() for x in input_msg]:
                    db_client = InitDBClient(**self.local_db_dict)
                    db_client.curr.execute("""DELETE FROM addcir WHERE user_id=%s""", user_id)
                    db_client.conn.commit()
                    db_client.conn.close()

                    body = f"등록된 모든 반복거래 설정이 삭제되었습니다.\n\n"
                    # Load currently registered addcir df
                    body += f"<b>현재 등록된 반복거래</b>"
                    db_client = InitDBClient(**self.local_db_dict)
                    db_client.curr.execute("""SELECT * FROM addcir WHERE user_id=%s""", user_id)
                    user_addcir_df = pd.DataFrame(db_client.curr.fetchall()).reset_index(drop=True)
                    user_addcir_df = user_addcir_df.where(user_addcir_df.notnull(), None)
                    db_client.conn.close()
                    body += self.show_addcir_list(user_addcir_df)
                    if len(user_addcir_df) != 0:
                        reply_markup = rmcir_InlineKeyboardButton(user_addcir_df, user_id)
                    else:
                        reply_markup = None
                    # send message
                    self.bot.send_thread_split_by_number(user_id, body, reply_markup=reply_markup)
                    return

                input_addcir_display_id_list = [x for x in input_msg]

                db_client = InitDBClient(**self.local_db_dict)
                for addcir_display_id in input_addcir_display_id_list:
                    try:
                        addcir_display_id = int(addcir_display_id)
                        addcir_redis_uuid = display_id_to_redis_uuid(user_id, self.snatcher.addcir_df, addcir_display_id)
                    except:
                        body = f"삭제는 코인이름이 아닌, 반복ID 를 입력해 주셔야 합니다.\n"
                        body += f"/rmcir 을 입력하여 사용법을 확인 해 주세요."
                        self.bot.send_thread(chat_id=user_id, text=body)
                        db_client.conn.close()
                        return
                    # res = db_client.curr.execute("""SELECT * FROM addcir WHERE redis_uuid=%s""", addcir_redis_uuid)
                    # if res == 0:
                    if addcir_redis_uuid is None:
                        body = f"반복ID: {addcir_display_id} 는 /addcir 에 등록되어 있지 않습니다."
                        body += f"/rmcir 을 입력하여 사용법을 확인 해 주세요."
                        self.bot.send_thread(chat_id=user_id, text=body)
                        db_client.conn.close()
                        return
                    db_client.curr.execute("""DELETE FROM addcir WHERE redis_uuid=%s""", (addcir_redis_uuid))
                    db_client.conn.commit()
                db_client.conn.close()

                body = f"반복ID: {', '.join(input_addcir_display_id_list)}가 반복거래 리스트에서 삭제되었습니다.\n\n"
                # Load currently registered addcir df
                body += f"<b>현재 등록된 반복거래</b>"
                db_client = InitDBClient(**self.local_db_dict)
                db_client.curr.execute("""SELECT * FROM addcir WHERE user_id=%s""", user_id)
                user_addcir_df = pd.DataFrame(db_client.curr.fetchall()).reset_index(drop=True)
                user_addcir_df = user_addcir_df.where(user_addcir_df.notnull(), None)
                db_client.conn.close()
                body += self.show_addcir_list(user_addcir_df)
                if len(user_addcir_df) != 0:
                    reply_markup = rmcir_InlineKeyboardButton(user_addcir_df, user_id)
                else:
                    reply_markup = None
                # send message
                self.bot.send_thread_split_by_number(user_id, body, reply_markup=reply_markup)
                return
            except Exception as e:
                self.telegram_bot_logger.error(f"rmcir|{traceback.format_exc()}")
                body = f"서비스에 불편을 드려 죄송합니다. 일시적인 오류가 발생했습니다. 관리자에게 문의 해 주세요. (@charlie1155)\n"
                body += f"error: {e}"
                self.bot.send_thread(chat_id=user_id, text=body)
                return
        rmcir_thread_th = Thread(target=rmcir_thread, daemon=True)
        rmcir_thread_th.start()
    
    def showcir(self, update, context):
        def showcir_thread():
            self.get_log('showcir', update, context)
            # Payment check
            user_id = update.effective_chat.id
            auth = self.authorize(user_id)
            if auth is False:
                return
            try:
                if context.args == []:
                    body = f"/showcir 명령어를 이용하여 /addcir 에 등록된 반복거래 중 원하는 코인의 거래들만 조회할 수 있습니다.\n"
                    body += f"코인심볼 입력 시, 김프거래 뿐만 아니라, <b>테더환산가로 등록된 자동거래도 같이 조회</b>됩니다.\n"
                    body += f"ex) /showcir btc"
                    self.bot.send_thread(chat_id=user_id, text=body, parse_mode=telegram.ParseMode.HTML)
                    return

                input_msg = ''.join(context.args).split(',')
                input_msg = [x.upper() for x in input_msg]

                if len(input_msg) != 1:
                    body = f"코인심볼은 하나만 입력 해 주세요."
                    self.bot.send_thread(chat_id=user_id, text=body)
                    return
                
                if input_msg[0].replace('USDT', '') not in [x.replace('-USDT-SWAP', '') for x in self.get_both_listed_okx_symbols()]:
                    body = f"{input_msg[0].replace('USDT', '')}은 업비트와 OKX USD-M 선물시장에 동시상장된 코인이 아닙니다."
                    self.bot.send_thread(chat_id=user_id, text=body)
                    return

                # Passed validation
                input_symbol = input_msg[0].replace('USDT', '')
                db_client = InitDBClient(**self.local_db_dict)
                db_client.curr.execute("""SELECT * FROM addcir WHERE user_id=%s""", user_id)
                fetched_addcir_df = pd.DataFrame(db_client.curr.fetchall())
                fetched_addcir_df = fetched_addcir_df.where(fetched_addcir_df.notnull(), None)
                db_client.conn.close()
                if len(fetched_addcir_df) == 0:
                    body = f"등록된 /addcir 설정이 존재하지 않습니다."
                    self.bot.send_thread(chat_id=user_id, text=body)
                    return
                filtered_fetched_addcir_df = fetched_addcir_df[fetched_addcir_df['symbol'].str.contains(input_symbol)].reset_index(drop=True)
                if len(filtered_fetched_addcir_df) == 0:
                    body = f"등록된 {input_symbol} /addcir 설정이 존재하지 않습니다."
                    self.bot.send_thread(chat_id=user_id, text=body)
                    return

                body = f"<b>현재 감지리스트 ({input_symbol})</b>\n"
                body += self.show_addcir_list(filtered_fetched_addcir_df)
                # send message
                self.bot.send_thread_split_by_number(user_id, body)
                return
            except Exception as e:
                self.telegram_bot_logger.error(f"showcir|{traceback.format_exc()}")
                body = f"서비스에 불편을 드려 죄송합니다. 일시적인 오류가 발생했습니다. 관리자에게 문의 해 주세요. (@charlie1155)\n"
                body += f"error: {e}"
                self.bot.send_thread(chat_id=user_id, text=body)
                return
        showcir_thread_th = Thread(target=showcir_thread, daemon=True)
        showcir_thread_th.start()
      
    def alarm(self, update, context):
        def alarm_thread(): 
            self.get_log('alarm', update, context)
            # Payment check
            user_id = update.effective_chat.id
            auth = self.authorize(user_id)
            if auth is False:
                return
            try:
                # Load user info from DB
                db_client = InitDBClient(**self.local_db_dict)
                db_client.curr.execute("""SELECT * FROM user_info WHERE user_id = %s""", user_id)
                fetched = db_client.curr.fetchall()
                db_client.conn.close()

                input_msg = ''.join(context.args).split(',')
                user_id = update.effective_chat.id
                
                if context.args == []:
                    user_alarm_num = pd.DataFrame(fetched)['alarm_num'].values[0]
                    user_alarm_period = pd.DataFrame(fetched)['alarm_period'].values[0]

                    body = f'현재 알람 설정: {user_alarm_num}회, {user_alarm_period}초 간격'
                    body += f'\n\n알람 메세지의 횟수와 전송 간격을 설정하는 명령어 입니다.'
                    body += f'\n설정된 알람이 작동될 때, 알람메세지를 중복으로 받고싶은 경우 아래와 같이 설정하여 사용하세요.'
                    body += f'\n설정된 횟수와 간격은 모든 알람에 적용됩니다.'
                    body += f'\n/alarm 숫자(횟수), 숫자(간격: 초) 형식으로 입력 해 주세요.'
                    body += f'\nex1) /alarm 5, 3  -> 5번 3초 간격'
                    body += f'\nex2) /alarm 3, 1 -> 3번 1초 간격'
                    self.bot.send_thread(chat_id=user_id, text=body)
                    return

                if len(input_msg) != 2:
                    body = f'잘못된 입력입니다.'
                    body += f'\n/alarm 을 입력하여 올바른 사용법을 확인 해 주세요.'
                    self.bot.send_thread(chat_id=user_id, text=body)
                    return
                
                try:
                    alarm_num = int(input_msg[0])
                    alarm_period = int(input_msg[1])
                except:
                    body = f'잘못된 입력입니다. 1 이상의 정수만 입력이 가능합니다.'
                    body += f'\n/alarm 을 입력하여 올바른 사용법을 확인 해 주세요.'
                    self.bot.send_thread(chat_id=user_id, text=body)
                    return

                if (alarm_num < 1) or (alarm_period < 1):
                    body = f'1 미만의 숫자는 입력하실 수 없습니다.'
                    body += f'\n/alarm 을 입력하여 올바른 사용법을 확인 해 주세요.'
                    self.bot.send_thread(chat_id=user_id, text=body)
                    return

                db_client = InitDBClient(**self.local_db_dict)
                db_client.curr.execute("""UPDATE user_info SET alarm_num=%s, alarm_period=%s WHERE user_id=%s""", (alarm_num, alarm_period, user_id))
                db_client.conn.commit()
                db_client.conn.close()
                body = f'정상적으로 설정되었습니다.'
                body += f'\n알람횟수: {alarm_num}회, 알람간격: {alarm_period}초'
                self.bot.send_thread(chat_id=user_id, text=body)
                return
            except Exception as e:
                self.telegram_bot_logger.error(f"alarm|{traceback.format_exc()}")
                body = f"서비스에 불편을 드려 죄송합니다. 일시적인 오류가 발생했습니다. 관리자에게 문의 해 주세요. (@charlie1155)\n"
                body += f"error: {e}"
                self.bot.send_thread(chat_id=user_id, text=body)
                return
        alarm_thread_th = Thread(target=alarm_thread, daemon=True)
        alarm_thread_th.start()

    def lev(self, update, context):
        def lev_thread():
            self.get_log('lev', update, context)
            user_id = update.effective_chat.id
            # Payment check
            auth = self.authorize(user_id)
            if auth is False:
                return
            try:
                input_msg = ''.join(context.args).split(',')
                if context.args == []:
                    db_client = InitDBClient(**self.local_db_dict)
                    db_client.curr.execute("""SELECT okx_leverage,okx_cross FROM user_info WHERE user_id=%s""", user_id)
                    fetched_dict = db_client.curr.fetchall()[0]
                    okx_leverage = fetched_dict['okx_leverage']
                    okx_cross = fetched_dict['okx_cross']
                    if okx_cross == 0:
                        okx_cross_str = "격리(Isolated)"
                    elif okx_cross == 1:
                        okx_cross_str = "교차(Cross)"
                    else:
                        okx_cross_str = None
                    db_client.conn.close()
                    body = f"/lev 명령어를 통해 김프 자동매매 시 OKX에 적용될 마진모드와 레버리지를 설정하실 수 있습니다.\n"
                    body += f"기본설정은 격리마진모드이며, /lev cross 입력 시, 교차마진모드로 설정됩니다.\n"
                    body += f"격리마진모드로 되돌아 가시려면, /lev isolated 를 입력하세요.\n"
                    body += f"설정된 레버리지는 설정 즉시 OKX에서 적용되는 것은 아니며, 김프거래에 진입할 때 적용됩니다.\n"
                    body += f"레버리지 배수는 /lev 배수(숫자) 로 설정가능합니다.\n"
                    body += f"ex) /lev 1, /lev 5\n"
                    body += f"기본설정은 레버리지 1배이며, 레버리지는 1배 부터 최대 25배 까지 설정 가능합니다.\n"
                    body += f"높은 배율의 레버리지를 설정할 경우 의도치 않은 청산의 위험이 커지므로 주의하세요.\n"
                    body += f"격리마진모드일 경우, 청산가에 가까워지면 코인봇이 모니터링 하여 경고메세지를 발송하지만 자동으로 정리하지는 않습니다.\n"
                    body += f"교차마진모드일 경우, 청산가가 변동하기 때문에, 코인봇이 청산가 모니터링을 하지 않습니다."
                    body += f"\n\n<b>현재 설정된 레버리지: {okx_leverage}배</b>\n"
                    body += f"마진모드 : <b>{okx_cross_str}</b>모드"
                    self.bot.send_thread(chat_id=user_id, text=body, parse_mode=telegram.ParseMode.HTML)
                    return

                if len(input_msg) != 1:
                    body = f"잘못된 입력입니다. /lev 를 입력하여 사용법을 확인 해 주세요."
                    self.bot.send_thread(chat_id=user_id, text=body)
                    return

                if input_msg[0].lower() == 'cross':
                    db_client = InitDBClient(**self.local_db_dict)
                    db_client.curr.execute("""UPDATE user_info SET okx_cross=%s WHERE user_id=%s""", (1, user_id))
                    db_client.conn.commit()
                    db_client.conn.close()
                    body = f"OKX의 마진모드가 교차(Cross)모드로 설정되었습니다."
                    self.bot.send_thread(chat_id=user_id, text=body)
                    return
                
                if input_msg[0].lower() == 'isolated':
                    db_client = InitDBClient(**self.local_db_dict)
                    db_client.curr.execute("""UPDATE user_info SET okx_cross=%s WHERE user_id=%s""", (0, user_id))
                    db_client.conn.commit()
                    db_client.conn.close()
                    body = f"OKX의 마진모드가 격리(Isolated)모드로 설정되었습니다."
                    self.bot.send_thread(chat_id=user_id, text=body)
                    return

                try:
                    input_lev = int(input_msg[0])
                except:
                    body = f"잘못된 입력입니다. /lev 를 입력하여 사용법을 확인 해 주세요."
                    self.bot.send_thread(chat_id=user_id, text=body)
                    return

                if input_lev < 1 or input_lev > 25:
                    body = f"레버리지는 1이상 25이하의 정수만 입력이 가능합니다."
                    self.bot.send_thread(chat_id=user_id, text=body)
                    return    

                db_client = InitDBClient(**self.local_db_dict)
                db_client.curr.execute("""UPDATE user_info SET okx_leverage=%s WHERE user_id=%s""", (input_lev, user_id))
                db_client.conn.commit()
                db_client.conn.close()

                body = f"OKX 레버리지가 {input_lev}로 설정되었습니다."
                self.bot.send_thread(chat_id=user_id, text=body)
                return
            except Exception as e:
                self.telegram_bot_logger.error(f"lev|{traceback.format_exc()}")
                body = f"서비스에 불편을 드려 죄송합니다. 일시적인 오류가 발생했습니다. 관리자에게 문의 해 주세요. (@charlie1155)\n"
                body += f"error: {e}"
                self.bot.send_thread(chat_id=user_id, text=body)
                return
        lev_thread_th = Thread(target=lev_thread, daemon=True)
        lev_thread_th.start()
    
    def mar(self, update, context):
        def mar_thread():
            self.get_log('mar', update, context)
            user_id = update.effective_chat.id
            # Payment check
            auth = self.authorize(user_id)
            if auth is False:
                return
            try:
                input_msg = ''.join(context.args).split(',')
                if context.args == []:
                    # Load margin monitor settings
                    user_margin_monitor = self.snatcher.userinfo_df[self.snatcher.userinfo_df['user_id']==user_id]['okx_margin_call'].values[0]
                    if user_margin_monitor == None:
                        mar_str = '청산 모니터링 기능 비활성'
                    elif user_margin_monitor == 1:
                        mar_str = '청산 경고 메시지 발신'
                    elif user_margin_monitor == 2:
                        mar_str = '청산 경고 메시지 발신 및 김프거래 자동정리'
                    else:
                        mar_str = '에러'

                    body = f"/mar 명령어로 OKX에 진입되어 있는 코인의 마진콜 메세지(청산경고)를 수신하거나,\n"
                    body += f"수신과 동시에 진입된 OKX와 업비트의 포지션을 자동정리하도록 설정할 수 있습니다.\n"
                    body += f"단순히 마진콜 경고메세지 수신만을 원하시면 /mar 1 을 입력하시고\n"
                    body += f"ex) /mar 1\n"
                    body += f"마진콜 경고메세지 수신 시, OKX와 업비트 포지션의 자동정리를 원하시면(김프매매탈출) /mar 2 을 입력하세요.\n"
                    body += f"ex2) /mar 2\n"
                    body += f"마진콜 모니터링 기능을 해제 하시려면(설정초기화) /mar reset 을 입력하세요.\n"
                    body += f"거래량 폭발로 가격이 급등(급락)하는 경우, 마진콜 메세지를 받음과 동시에 OKX에서 청산이 일어날 수 있습니다.\n\n\n"
                    body += f"<b>OKX 청산 모니터링 설정상태</b>\n"
                    body += f"현재설정: <b>{mar_str}</b>"
                    self.bot.send_thread(chat_id=user_id, text=body, parse_mode=telegram.ParseMode.HTML)
                    return

                if len(input_msg) != 1:
                    body = f"잘못된 입력입니다. /mar 을 입력하여 사용법을 확인 해 주세요."
                    self.bot.send_thread(chat_id=user_id, text=body)
                    return

                if input_msg[0].lower() == 'reset':
                    db_client = InitDBClient(**self.local_db_dict)
                    db_client.curr.execute("""UPDATE user_info SET okx_margin_call=%s WHERE user_id=%s""", (None, user_id))
                    db_client.conn.commit()
                    db_client.conn.close()
                    body = f"OKX 마진콜 모니터링이 정상적으로 해제되었습니다."
                    self.bot.send_thread(chat_id=user_id, text=body)
                    return

                try:
                    monitor_mode = int(input_msg[0])
                    # 1 -> only send margin call message
                    # 2 -> send margin call message & auto exit
                    if monitor_mode not in [1, 2]:
                        body = f"잘못된 입력 값입니다.\n"
                        body += f"/mar 을 입력하여 사용법을 확인 해 주세요."
                        self.bot.send_thread(chat_id=user_id, text=body)
                        return
                except:
                    body = f"잘못된 입력입니다. /mar 을 입력하여 사용법을 확인 해 주세요."
                    self.bot.send_thread(chat_id=user_id, text=body)
                    return
                
                # Passed all validation
                if monitor_mode == 1:
                    db_client = InitDBClient(**self.local_db_dict)
                    db_client.curr.execute("""UPDATE user_info SET okx_margin_call=%s WHERE user_id=%s""", (1, user_id))
                    db_client.conn.commit()
                    db_client.conn.close()
                    body = f"마진콜 모니터링 모드가 <b>마진콜 메세지만 수신</b>으로 설정되었습니다.\n"
                    body += f"OKX에 진입된 코인이 청산가에 가까워지면, 마진콜 경고메세지가 수신됩니다."
                    self.bot.send_thread(chat_id=user_id, text=body, parse_mode=telegram.ParseMode.HTML)
                    return
                elif monitor_mode == 2:
                    db_client = InitDBClient(**self.local_db_dict)
                    db_client.curr.execute("""UPDATE user_info SET okx_margin_call=%s WHERE user_id=%s""", (2, user_id))
                    db_client.conn.commit()
                    db_client.conn.close()
                    body = f"마진콜 모니터링 모드가 <b>마진콜 메세지 수신 및 김프거래 탈출</b>로 설정되었습니다.\n"
                    body += f"OKX에 진입된 코인이 청산가에 가까워지면, 마진콜 경고메세지가 수신됨과 동시에 OKX와 업비트의 진입 물량을 정리합니다."
                    self.bot.send_thread(chat_id=user_id, text=body, parse_mode=telegram.ParseMode.HTML)
                    return
            except Exception as e:
                self.telegram_bot_logger.error(f"mar|{traceback.format_exc()}")
                body = f"서비스에 불편을 드려 죄송합니다. 일시적인 오류가 발생했습니다. 관리자에게 문의 해 주세요. (@charlie1155)\n"
                body += f"error: {e}"
                self.bot.send_thread(chat_id=user_id, text=body)
                return
        mar_thread_th = Thread(target=mar_thread, daemon=True)
        mar_thread_th.start()
    
    def omit(self, update, context):
        def omit_thread():
            self.get_log('omit', update, context)
            user_id = update.effective_chat.id
            # Payment check
            auth = self.authorize(user_id)
            if auth is False:
                return
            try:
                user_on_off = self.snatcher.userinfo_df[self.snatcher.userinfo_df['user_id']==user_id]['on_off'].values[0]
                if user_on_off == 1:
                    db_client = InitDBClient(**self.local_db_dict)
                    db_client.curr.execute("""UPDATE user_info SET on_off=%s WHERE user_id=%s""", (0, user_id))
                    db_client.conn.commit()
                    body = f"기능 설명이 <b>꺼짐</b>으로 설정되었습니다.\n"
                    body += f"addcoin과 addcir, addint에 대한 설명이 표시되지 않습니다.\n"
                    body += f"다시 설명을 키시려면 /omit 을 다시 한 번 입력해 주세요."
                    self.bot.send_thread(chat_id=user_id, text=body, parse_mode=telegram.ParseMode.HTML)
                    db_client.conn.close()
                    return
                else:
                    db_client = InitDBClient(**self.local_db_dict)
                    db_client.curr.execute("""UPDATE user_info SET on_off=%s WHERE user_id=%s""", (1, user_id))
                    db_client.conn.commit()
                    body = f"기능 설명이 <b>켜짐</b>으로 설정되었습니다.\n"
                    body += f"addcoin과 addcir, addint에 대한 설명이 표시됩니다.\n"
                    body += f"설명을 끄시려면 /omit 을 입력해 주세요."
                    self.bot.send_thread(chat_id=user_id, text=body, parse_mode=telegram.ParseMode.HTML)
                    db_client.conn.close()
                    return
            except Exception as e:
                self.telegram_bot_logger.error(f"omit|{traceback.format_exc()}")
                body = f"서비스에 불편을 드려 죄송합니다. 일시적인 오류가 발생했습니다. 관리자에게 문의 해 주세요. (@charlie1155)\n"
                body += f"error: {e}"
                self.bot.send_thread(chat_id=user_id, text=body)
                return
        omit_thread_th = Thread(target=omit_thread, daemon=True)
        omit_thread_th.start()
    
    def safe(self, update, context):
        def safe_thread():
            self.get_log('safe', update, context)
            user_id = update.effective_chat.id
            # Payment check
            auth = self.authorize(user_id)
            if auth is False:
                return
            try:
                user_safe_reverse = self.snatcher.userinfo_df[self.snatcher.userinfo_df['user_id']==user_id]['safe_reverse'].values[0]
                if user_safe_reverse == 1:
                    db_client = InitDBClient(**self.local_db_dict)
                    db_client.curr.execute("""UPDATE user_info SET safe_reverse=%s WHERE user_id=%s""", (0, user_id))
                    db_client.conn.commit()
                    body = f"/safe 명령어로 역매매 안전기능을 키고 끌 수 있습니다.\n"
                    body += f"의도치 않은 에러로 인해, 김프거래 시 한쪽만 체결되는 경우,\n"
                    body += f"역매매 안전기능을 켜 놓으면, 봇이 혼자 체결된 거래소의 포지션을 역매매를 하여 체결되기 전으로 되돌립니다.\n"
                    body += f"즉, 김프거래 진입 시에 한 쪽 거래소에서 에러가 발생하면, 반대쪽 거래소의 정상 체결물량을 즉시 정리하며,\n"
                    body += f"김프거래 탈출 시에 한 쪽 거래소에서 에러가 발생하면, 반대쪽 거래소의 정상 정리물량을 즉시 재진입 합니다.\n"
                    body += f"따라서, OKX-업비트 간의 헷지가 풀려서 발생하는 손실을 최소화할 수 있습니다.\n\n"
                    body += f"<b>설정 상태</b>\n"
                    body += f"역매매 안전기능이 <b>꺼짐</b>으로 설정되었습니다.\n"
                    body += f"기능을 키시려면 /safe 을 다시 한 번 입력해 주세요."
                    self.bot.send_thread(chat_id=user_id, text=body, parse_mode=telegram.ParseMode.HTML)
                    return
                else:
                    db_client = InitDBClient(**self.local_db_dict)
                    db_client.curr.execute("""UPDATE user_info SET safe_reverse=%s WHERE user_id=%s""", (1, user_id))
                    db_client.conn.commit()
                    body = f"/safe 명령어로 역매매 안전기능을 키고 끌 수 있습니다.\n"
                    body += f"의도치 않은 에러로 인해, 김프거래 시 한쪽만 체결되는 경우,\n"
                    body += f"역매매 안전기능을 켜 놓으면, 봇이 혼자 체결된 거래소의 포지션을, 체결되기 전으로 역매매를 하여 되돌립니다.\n"
                    body += f"즉, 김프거래 진입 시에 한 쪽 거래소에서 에러가 발생하면, 반대쪽 거래소의 정상 체결물량을 즉시 정리하며,\n"
                    body += f"김프거래 탈출 시에 한 쪽 거래소에서 에러가 발생하면, 반대쪽 거래소의 정상 정리물량을 즉시 재진입 합니다.\n"
                    body += f"따라서, OKX-업비트 간의 헷지가 풀려서 발생하는 손실을 최소화할 수 있습니다.\n\n"
                    body += f"<b>설정 상태</b>\n"
                    body += f"역매매 안전기능이 <b>켜짐</b>으로 설정되었습니다.\n"
                    body += f"기능을 끄시려면 /safe 을 입력해 주세요.\n"
                    body += f"<b>주의!</b> /addcoin 을 통한 거래가 아닌, /exit 명령어를 이용한 수동 탈출 시에는, 역매매 안전기능 기능이 켜져 있어도 작동하지 않습니다."
                    self.bot.send_thread(chat_id=user_id, text=body, parse_mode=telegram.ParseMode.HTML)
                    return
            except Exception as e:
                self.telegram_bot_logger.error(f"safe|{traceback.format_exc()}")
                body = f"서비스에 불편을 드려 죄송합니다. 일시적인 오류가 발생했습니다. 관리자에게 문의 해 주세요. (@charlie1155)\n"
                body += f"error: {e}"
                self.bot.send_thread(chat_id=user_id, text=body)
                return
        safe_thread_th = Thread(target=safe_thread, daemon=True)
        safe_thread_th.start()

    def addcirl(self, update, context):
        def addcirl_thread():
            self.get_log('addcirl', update, context)
            user_id = update.effective_chat.id
            # Payment check
            auth = self.authorize(user_id)
            if auth is False:
                return
            try:
                if context.args == []:
                    body = f'/addcirl 명령어를 통해 /addcir <b>반복거래가 작동되는 김프</b>조건을 설정할 수 있습니다.\n'
                    body += f'/addcir 로 설정된 /addcoin 자동거래가 탈출 되었을 때, 특정 김프 이상에서는 /addcoin 이 재등록되지 않게 함으로써, 자동 재등록으로 인해 김프 고점에서 물리는 일을 방지 할 수 있습니다.\n'
                    body += f"조건으로 적용되는 김프는 /kp 입력 시 확인가능한, <b>거래량 가중평균 김프</b>입니다.\n"
                    body += f"예를 들어, /addcirl 5 로 설정하면 평균김프가 5% 이상일 때는 /addcir 작동을 비활성화 시키며,\n"
                    body += f"평균김프가 5% 밑으로 내려와야만 /addcir 가 활성화되어 /addcoin 탈출 시, 재등록 됩니다.\n"
                    body += f"조건 설정을 삭제하시려면 /addcirl reset 을 입력하세요.\n\n"
                    db_client = InitDBClient(**self.local_db_dict)
                    db_client.curr.execute("""SELECT addcir_limit FROM user_info WHERE user_id=%s""", user_id)
                    user_addcir_limit = db_client.curr.fetchall()[0]['addcir_limit']
                    db_client.conn.close()
                    if user_addcir_limit == None:
                        addcir_str = '없음'
                    elif user_addcir_limit <= 500:
                        addcir_str = f"평균<b>김프</b>가 <b>{user_addcir_limit}% 이상</b>일 때, addcir 비활성화"
                    elif user_addcir_limit > 500:
                        addcir_str = f"평균 <b>테더환산가</b>가 <b>{user_addcir_limit}원 이상</b>일 때, addcir 비활성화"
                    else:
                        addcir_str = f'Error: {user_addcir_limit}'

                    body += f"<b>현재 설정된 값</b>\n"
                    body += f"{addcir_str}"
                    self.bot.send_thread(chat_id=user_id, text=body, parse_mode=telegram.ParseMode.HTML)
                    return
                input_msg = ''.join(context.args).split(',')
                if len(input_msg) != 1:
                    body = f"잘못된 입력입니다. /addcirl 을 입력하여 사용법을 확인하세요."
                    self.bot.send_thread(chat_id=user_id, text=body)
                    return

                if input_msg[0].upper() == 'RESET':
                    db_client = InitDBClient(**self.local_db_dict)
                    db_client.curr.execute("""UPDATE user_info SET addcir_limit=%s WHERE user_id=%s""", (None, user_id))
                    db_client.conn.commit()
                    db_client.conn.close()
                    body = f"/addcir 반복거래 실행조건 설정이 초기화되었습니다."
                    self.bot.send_thread(chat_id=user_id, text=body)
                    return

                try:
                    input_num = float(input_msg[0])
                except:
                    body = f"숫자만 입력 가능합니다. /addcirl 을 입력하여 사용법을 확인하세요."
                    self.bot.send_thread(chat_id=user_id, text=body)
                    return

                if input_num >= 100:
                    body = f"입력 값: {input_num} 은 너무 큰 숫자입니다.\n"
                    body += f"/addcirl 을 입력하여 사용법을 확인하세요."
                    self.bot.send_thread(chat_id=user_id, text=body)
                    return
                
                # Passed all validation
                # If the number is less than 500, consider it kimp.
                if input_num <= 500:
                    usdt_flag = False
                    temp_str = "평균<b>김프</b>"
                    temp_str2 = "%"
                else:
                    usdt_flag = True
                    temp_str = "평균 <b>테더환산가</b>"
                    temp_str2 = '원'
                # Save the data into the DB
                db_client = InitDBClient(**self.local_db_dict)
                db_client.curr.execute("""UPDATE user_info SET addcir_limit=%s WHERE user_id=%s""", (input_num, user_id))
                db_client.conn.commit()
                db_client.conn.close()
                body = f"설정이 저장되었습니다.\n"
                body += f"{temp_str}가 <b>{input_num}{temp_str2} 이하</b>일 때에만 /addcir 반복거래가 활성화 됩니다."
                self.bot.send_thread(chat_id=user_id, text=body, parse_mode=telegram.ParseMode.HTML)
                return
            except Exception as e:
                self.telegram_bot_logger.error(f"addcirl|{traceback.format_exc()}")
                body = f"서비스에 불편을 드려 죄송합니다. 일시적인 오류가 발생했습니다. 관리자에게 문의 해 주세요. (@charlie1155)\n"
                body += f"error: {e}"
                self.bot.send_thread(chat_id=user_id, text=body)
                return
        addcirl_thread_th = Thread(target=addcirl_thread, daemon=True)
        addcirl_thread_th.start()
    
    def addcirn(self, update, context):
        def addcirn_thread():
            self.get_log('addcirn', update, context)
            user_id = update.effective_chat.id
            # Payment check
            auth = self.authorize(user_id)
            if auth is False:
                return
            try:
                if context.args == []:
                    body = f'/addcirn 명령어를 통해 /addcir <b>반복거래가 작동되는 최대 싸이클 횟수</b>를 설정할 수 있습니다.\n'
                    body += f"예를 들어, /addcirn 0 으로 설정하는 경우, /addcir 설정 시 최초 자동등록된 /addcoin 이 탈출된 이후,\n<b>더 이상 /addcoin 이 재등록되지 않습니다.</b>\n"
                    body += f'/addcirn 1 로 설정하는 경우, /addcir 로 설정된 최초 /addcoin 의 진입 및 탈출 이후 <b>추가적으로 1회 더 재등록</b> 됩니다.\n'
                    body += f"횟수 제한을 초기화 하시려면 /addcirn reset 을 입력하세요.\n\n"
                    db_client = InitDBClient(**self.local_db_dict)
                    db_client.curr.execute("""SELECT addcir_num_limit FROM user_info WHERE user_id=%s""", user_id)
                    user_addcir_num_limit = db_client.curr.fetchall()[0]['addcir_num_limit']
                    db_client.conn.close()
                    if user_addcir_num_limit == None:
                        addcir_str = '없음'
                    elif user_addcir_num_limit == 0:
                        addcir_str = f"/addcir 설정으로 최초 자동등록되는 /addcoin 의 진입 및 탈출 이후,\n"
                        addcir_str += f"/addcoin 이 자동 재등록되지 않습니다."
                    else:
                        addcir_str = f"/addcir(반복거래) 최대 싸이클 횟수: {user_addcir_num_limit}회"

                    body += f"<b>현재 설정된 값</b>\n"
                    body += f"{addcir_str}"
                    self.bot.send_thread(chat_id=user_id, text=body, parse_mode=telegram.ParseMode.HTML)
                    return
                input_msg = ''.join(context.args).split(',')
                if len(input_msg) != 1:
                    body = f"잘못된 입력입니다. /addcirl 을 입력하여 사용법을 확인하세요."
                    self.bot.send_thread(chat_id=user_id, text=body)
                    return

                if input_msg[0].upper() == 'RESET':
                    db_client = InitDBClient(**self.local_db_dict)
                    db_client.curr.execute("""UPDATE user_info SET addcir_num_limit=%s WHERE user_id=%s""", (None, user_id))
                    db_client.conn.commit()
                    db_client.conn.close()
                    body = f"/addcir(반복거래) 최대 싸이클 횟수 제한이 초기화되었습니다."
                    self.bot.send_thread(chat_id=user_id, text=body)
                    return

                try:
                    input_num = int(input_msg[0])
                except:
                    body = f"숫자만 입력 가능합니다. /addcirn 을 입력하여 사용법을 확인하세요."
                    self.bot.send_thread(chat_id=user_id, text=body)
                    return

                if input_num < 0:
                    body = f"0 미만인 음수는 입력하실 수 없습니다.\n"
                    body += f"/addcirn 을 입력하여 사용법을 확인하세요."
                    self.bot.send_thread(chat_id=user_id, text=body)
                    return
                
                # Passed all validation  
                # Save the data into the DB
                db_client = InitDBClient(**self.local_db_dict)
                db_client.curr.execute("""UPDATE user_info SET addcir_num_limit=%s WHERE user_id=%s""", (input_num, user_id))
                db_client.conn.commit()
                db_client.conn.close()
                body = f"설정이 저장되었습니다.\n"
                if input_num == 0:
                    body += f"/addcir 설정으로 최초 자동등록되는 /addcoin 의 진입 및 탈출 이후,\n"
                    body += f"/addcoin 이 자동 재등록되지 않습니다."
                else:
                    body += f"/addcir 설정으로 발동되는 /addcoin 반복거래가 최대 {input_num}회 까지만 실행됩니다."
                self.bot.send_thread(chat_id=user_id, text=body, parse_mode=telegram.ParseMode.HTML)
                return
            except Exception as e:
                self.telegram_bot_logger.error(f"addcirn|{traceback.format_exc()}")
                body = f"서비스에 불편을 드려 죄송합니다. 일시적인 오류가 발생했습니다. 관리자에게 문의 해 주세요. (@charlie1155)\n"
                body += f"error: {e}"
                self.bot.send_thread(chat_id=user_id, text=body)
                return
        addcirn_thread_th = Thread(target=addcirn_thread, daemon=True)
        addcirn_thread_th.start()
    # Need to be checked
    def server_check(self, update, context):
        def server_check_thread():
            self.get_log('server_check', update, context, 'admin')
            user_id = update.effective_chat.id
            if user_id != self.admin_id:
                return
            try:
                input_msg = ''.join(context.args).split(',')
                if context.args == []:
                    db_client = InitDBClient(**self.remote_db_dict)
                    db_client.curr.execute("""SELECT * FROM server_check""")
                    server_check_df = pd.DataFrame(db_client.curr.fetchall())
                    server_check_df = server_check_df.where(server_check_df.notnull(), None)
                    db_client.conn.close()
                    body = f"/server_check 거래소이름,서버점검시작시간_서버점검종료시간 입력 시, 해당시간동안 서버체크 변수 ON\n"
                    body += f"/server_check reset 입력 시, 서버점검 NULL 초기화로 서버시작\n"
                    body += f"ex) /server_check upbit,20210826T23:00_20210827T02:00\n\n"
                    body += f"현재 등록된 서버점검"

                    for row_tup in server_check_df.iterrows():
                        index = row_tup[0]
                        row = row_tup[1]
                        body += f"\n거래소: {row['exchange']}, 시작: {row['server_check_start']}, 종료: {row['server_check_end']}, Flag: {row['server_check_flag']}"
                    self.bot.send_thread(chat_id=user_id, text=body)
                    return

                if len(input_msg) > 2:
                    body = f"Input Error!"
                    self.bot.send_thread(chat_id=user_id, text=body)
                    return

                if input_msg[0] == 'reset':
                    db_client = InitDBClient(**self.remote_db_dict)
                    fetch_num_upbit = db_client.curr.execute("""SELECT * FROM server_check WHERE exchange=%s""", 'upbit')
                    if fetch_num_upbit == 0:
                        db_client.curr.execute("""INSERT INTO server_check(datetime, exchange) VALUES(%s, %s)""",(datetime.datetime.now(), 'upbit'))
                    else:
                        db_client.curr.execute("""SELECT id FROM server_check WHERE exchange=%s""", "upbit")
                        upbit_id = db_client.curr.fetchall()[0]['id']
                        db_client.curr.execute("""UPDATE server_check SET datetime=%s, server_check_start=%s, server_check_end=%s, server_check_flag=%s WHERE id=%s""", (datetime.datetime.now(), None, None, None, upbit_id))
                        
                    fetch_num_okx = db_client.curr.execute("""SELECT * FROM server_check WHERE exchange=%s""", 'okx')
                    if fetch_num_okx == 0:
                        db_client.curr.execute("""INSERT INTO server_check(datetime, exchange) VALUES(%s, %s)""",(datetime.datetime.now(), 'okx'))
                    else:
                        db_client.curr.execute("""SELECT id FROM server_check WHERE exchange=%s""", "okx")
                        okx_id = db_client.curr.fetchall()[0]['id']
                        db_client.curr.execute("""UPDATE server_check SET datetime=%s, server_check_start=%s, server_check_end=%s, server_check_flag=%s WHERE id=%s""", (datetime.datetime.now(), None, None, None, okx_id))
                    db_client.conn.commit()
                    db_client.conn.close()

                    body = f"OKX와 업비트 서버점검 데이터가 초기화되었습니다."
                    self.bot.send_thread(chat_id=user_id, text=body)
                    return

                elif input_msg[0] == 'okx' or input_msg[0] == 'upbit':
                    exchange = input_msg[0]
                    server_check_time_list = input_msg[1].split('_')
                    start_time = datetime.datetime.strptime(server_check_time_list[0], "%Y%m%dT%H:%M")
                    end_time = datetime.datetime.strptime(server_check_time_list[1], "%Y%m%dT%H:%M")

                    db_client = InitDBClient(**self.remote_db_dict)
                    db_client.curr.execute("""UPDATE server_check SET server_check_start=%s, server_check_end=%s, server_check_flag=%s WHERE exchange=%s""", (start_time, end_time, -1, exchange))
                    db_client.conn.commit()
                    db_client.conn.close()  

                    body = f"{exchange.upper()}의 서버점검시간이 {start_time}에서 {end_time}로 예약되었습니다."
                    self.bot.send_thread(chat_id=user_id, text=body)
                    return

                else:
                    body = f"Input Error!"
                    self.bot.send_thread(chat_id=user_id, text=body)
                    return
            except Exception as e:
                self.telegram_bot_logger.error(f'server_check|{traceback.format_exc()}')
                body = f"서비스에 불편을 드려 죄송합니다. 일시적인 오류가 발생했습니다. 관리자에게 문의 해 주세요. (@charlie1155)\n"
                body += f"error: {e}"
                self.bot.send_thread(chat_id=user_id, text=body)
                return
        server_check_thread_th = Thread(target=server_check_thread, daemon=True)
        server_check_thread_th.start()
    
    def fundt(self, update, context):
        def fundt_thread():
            self.get_log('fundt', update, context)
            user_id = update.effective_chat.id
            # Payment check
            auth = self.authorize(user_id)
            if auth is False:
                return
            try:
                if context.args == []:
                    body = f'"/fundt 숫자" 명령어를 통해 현재 혹은 USDT마켓 펀딩률의 최근 n회 평균값을 확인하실 수 있습니다.'
                    body += f'\n/fundt 1 이라고 입력하실 경우 아직 펀딩이 진행되지 않은 이번 타임 펀딩률이 조회 됩니다.'
                    body += f'\nOKX의 펀딩률은 실시간으로 변할 수 있습니다.'
                    body += f'\n목록은 펀딩률을 기준, 내림차순으로 정렬됩니다.'
                    body += f'\n사용예시) /fundt 1, /fundt 3, /fundt 7'
                    self.bot.send_thread(chat_id=update.effective_chat.id, text=body)
                    return
                input_msg = ''.join(context.args).strip()
                try:
                    input_msg = int(input_msg)
                except:
                    body = f'잘못된 입력값입니다.'
                    body += f'\n 1이상의 숫자만 입력 가능합니다.'
                    self.bot.send_thread(chat_id=update.effective_chat.id, text=body)

                if input_msg <= 0:
                    body = f'잘못된 입력값입니다.'
                    body += f'\n 1이상의 숫자만 입력 가능합니다.'
                    self.bot.send_thread(chat_id=update.effective_chat.id, text=body)
                    return
                else:
                    tail_okx_funding_df = self.snatcher.funding_df[self.snatcher.funding_df['okx_symbol'].isin(self.get_both_listed_okx_symbols())].groupby('okx_symbol').tail(input_msg)
                    mean_okx_funding_df = tail_okx_funding_df.groupby('okx_symbol').agg('mean').reset_index()
                    mean_okx_funding_df = mean_okx_funding_df.rename(columns={'fundingrate':'usdt_avg'})
                    okx_fund_avg_df = mean_okx_funding_df

                    if input_msg == 1:
                        remaining_sec = (self.snatcher.funding_df['fundingtime'].iloc[-1] - datetime.datetime.now()).seconds
                        remaining_minutes = remaining_sec // 60
                        hours = remaining_minutes // 60
                        minutes = remaining_minutes % 60
                        seconds = remaining_sec % 60

                        string = f'이번 펀딩률({hours}시간 {minutes}분 남음)'
                    else:
                        string = f'최근 {input_msg}회 평균펀딩률'

                    okx_fund_avg_df = okx_fund_avg_df.sort_values(by=f'usdt_avg', ascending=False)
                    okx_fund_avg_df = okx_fund_avg_df.where(okx_fund_avg_df.notnull(), None)

                    body = u'\U0001F4CC'+'<b>OKX USDT SWAP(실시간 변동가능)</b>'
                    for row_tup in okx_fund_avg_df.iterrows():
                        row = row_tup[1]
                        body += f"\n<b>{row['okx_symbol']}</b>  |{string}: <b>{round(100*row['usdt_avg'],4)}%</b>"
                    self.bot.send_thread(chat_id=update.effective_chat.id, text=body, parse_mode=telegram.ParseMode.HTML)
            except Exception as e:
                self.telegram_bot_logger.error(f'fundt|{traceback.format_exc()}')
                body = f"서비스에 불편을 드려 죄송합니다. 일시적인 오류가 발생했습니다. 관리자에게 문의 해 주세요. (@charlie1155)\n"
                body += f"error: {e}"
                self.bot.send_thread(chat_id=user_id, text=body)
                return
        fundt_thread_th = Thread(target=fundt_thread, daemon=True)
        fundt_thread_th.start()

    def diff(self, update, context):
        def diff_thread():
            self.get_log('diff', update, context)
            user_id = update.effective_chat.id
            # Payment check
            auth = self.authorize(user_id)
            if auth is False:
                return
            try:
                user_diff = self.snatcher.userinfo_df[self.snatcher.userinfo_df['user_id']==user_id]['kimp_diff'].values[0]
                if user_diff == None:
                    diff_str = '등록된 감지설정 없음(감지 비활성화)'
                elif user_diff >= 0:
                    diff_str = f"김프가 평균김프보다 <b>{user_diff}% 이상 높은</b> 코인 감지"
                elif user_diff < 0:
                    diff_str = f"김프가 평균김프보다 <b>{user_diff}% 이상 낮은</b> 코인 감지"

                if context.args == []:
                    body = f'/diff 명령어를 통해 거래량가중평균김프와 괴리가 심한 코인들에 대한 감지기능을 설정할 수 있습니다.\n'
                    body += f'/diff 숫자(%) 형식으로 설정이 가능하며, 양수와 음수 둘다 가능합니다.\n'
                    body += f'ex1) /diff 3 == 김프가 평균김프보다 3% 이상 높은 코인 감지\n'
                    body += f'ex2) /diff -3 == 김프가 평균김프보다 3% 이상 낮은 코인 감지\n'
                    body += f"한 번 감지된 코인은 중복메세지 방지를 위해 3시간동안은 재감지되지 않습니다.\n"
                    body += f"3시간 텀을 초기화 시키시려면 /diff reset 을 입력하세요.\n"
                    body += f"감지설정을 비활성화 하시려면 /diff off 를 입력하세요.\n\n"
                    body += f"<b>현재 감지설정</b>\n"
                    body += f"{diff_str}"
                    self.bot.send_thread(chat_id=user_id, text=body, parse_mode=telegram.ParseMode.HTML)
                    return

                input_msg = ''.join(context.args).split(',')
                if len(input_msg) != 1:
                    body = f"잘못된 입력입니다. /diff 를 입력하여 사용법을 확인 해 주세요."
                    self.bot.send_thread(chat_id=user_id, text=body)
                    return

                if input_msg[0].upper() == 'OFF':
                    db_client = InitDBClient(**self.local_db_dict)
                    db_client.curr.execute("""UPDATE user_info SET kimp_diff=%s WHERE user_id=%s""", (None, user_id))
                    db_client.conn.commit()
                    db_client.curr.execute("""SELECT kimp_diff FROM user_info WHERE user_id=%s""", user_id)
                    fetched_diff = db_client.curr.fetchall()[0]['kimp_diff']
                    db_client.conn.close()
                    if fetched_diff == None:
                        diff_str = '등록된 감지설정 없음(감지 비활성화)'
                    elif fetched_diff >= 0:
                        diff_str = f"김프가 평균김프보다 <b>{fetched_diff}% 이상 높은</b> 코인 감지"
                    elif fetched_diff < 0:
                        diff_str = f"김프가 평균김프보다 <b>{str(fetched_diff).replace('-','')}% 이상 낮은</b> 코인 감지"
                    body = "<b>현재 감지설정</b>\n"
                    body += diff_str
                    self.bot.send_thread(chat_id=user_id, text=body, parse_mode=telegram.ParseMode.HTML)
                    return

                if input_msg[0].upper() == 'RESET':
                    db_client = InitDBClient(**self.local_db_dict)
                    db_client.curr.execute("""DELETE FROM kimp_diff WHERE user_id=%s""", user_id)
                    db_client.conn.commit()
                    db_client.conn.close()
                    body = f"3시간 중복감지 방지 데이터가 정상적으로 초기화 되었습니다."
                    self.bot.send_thread(chat_id=user_id, text=body)
                    return

                try:
                    input_diff = float(input_msg[0])
                except:
                    body = f"숫자만 입력이 가능합니다. /diff 를 입력하여 사용법을 확인 해 주세요."
                    self.bot.send_thread(chat_id=user_id, text=body)
                    return
                
                if input_diff == 0:
                    body = f"0은 설정할 수 없습니다. /diff 를 입력하여 사용법을 확인 해 주세요."
                    self.bot.send_thread(chat_id=user_id, text=body)
                    return

                # Passed validation
                # UPDATE kimp_diff into the database
                db_client = InitDBClient(**self.local_db_dict)
                db_client.curr.execute("""UPDATE user_info SET kimp_diff=%s WHERE user_id=%s""", (input_diff, user_id))
                db_client.conn.commit()
                db_client.curr.execute("""SELECT kimp_diff FROM user_info WHERE user_id=%s""", user_id)
                fetched_diff = db_client.curr.fetchall()[0]['kimp_diff']
                db_client.conn.close()

                if fetched_diff == None:
                    diff_str = '등록된 감지설정 없음(감지 비활성화)'
                elif fetched_diff >= 0:
                    diff_str = f"김프가 평균김프보다 <b>{fetched_diff}% 이상 높은</b> 코인 감지"
                elif fetched_diff < 0:
                    diff_str = f"김프가 평균김프보다 <b>{str(fetched_diff).replace('-','')}% 이상 낮은</b> 코인 감지"

                body = "<b>현재 감지설정</b>\n"
                body += diff_str
                self.bot.send_thread(chat_id=user_id, text=body, parse_mode=telegram.ParseMode.HTML)
                return

            except Exception as e:
                self.telegram_bot_logger.error(f"diff|{traceback.format_exc()}")
                body = f"서비스에 불편을 드려 죄송합니다. 일시적인 오류가 발생했습니다. 관리자에게 문의 해 주세요. (@charlie1155)\n"
                body += f"error: {e}"
                self.bot.send_thread(chat_id=user_id, text=body)
                return
        diff_thread_th = Thread(target=diff_thread, daemon=True)
        diff_thread_th.start()
    
    def pro(self, update, context):
        def pro_thread():
            self.get_log('pro', update, context)
            user_id = update.effective_chat.id
            # Payment check
            auth = self.authorize(user_id)
            if auth is False:
                return
            try:
                detail = False
                if context.args == []:
                    body = f'/pro 명령어를 통해 최근 n일 동안의 김프거래 손익을 확인할 수 있습니다.\n'
                    body += f'ex1) /pro 30\n'
                    body += f"/addcoin 기능을 활용하지 않은 <b>수동거래 혹은 정상탈출되지 않은 거래</b>는 손익에 반영되지 않습니다.\n"
                    body += f"손익은 업비트의 진입 탈출 원화손익(거래 수수료적용)과 OKX의 진입 탈출 달러손익(거래수수료 적용)을 거래소 별로 계산한 이후,\n"
                    body += f"각 거래 당시의 달러환율을 적용하여 계산됩니다.\n"
                    body += f"/pro n일 형식으로 내역 조회가 가능하며, 세부정보가 포함된 엑셀 형태로 다운받으시려면 'detail' 을 n일 뒤에 추가로 입력하세요.\n"
                    body += f'ex2) /pro 30, detail\n'
                    self.bot.send_thread(chat_id=user_id, text=body, parse_mode=telegram.ParseMode.HTML)
                    return

                input_msg = ''.join(context.args).split(',')
                input_msg = [x.upper() for x in input_msg]

                if 'DETAIL' in input_msg:
                    detail = True
                    input_msg = [x for x in input_msg if x != "DETAIL"]

                if len(input_msg) != 1:
                    body = f"잘못된 입력입니다. /pro 를 입력하여 사용법을 확인 해 주세요."
                    self.bot.send_thread(chat_id=user_id, text=body)
                    return

                try:
                    input_days = int(input_msg[0])
                    if input_days < 1:
                        body = f"최근 n일 값은 자연수만 입력이 가능합니다. /pro 를 입력하여 사용법을 확인 해 주세요."
                        self.bot.send_thread(chat_id=user_id, text=body)
                        return
                except:
                    body = f"최근 n일 값은 자연수만 입력이 가능합니다. /pro 를 입력하여 사용법을 확인 해 주세요."
                    self.bot.send_thread(chat_id=user_id, text=body)
                    return
                
                body = f"거래내역을 합산 중입니다.. 잠시만 기다려 주세요.."
                self.bot.send_thread(chat_id=user_id, text=body)
                recent_profit_df, detailed_recent_profit_df = self.data_processor.get_user_profit_df(user_id, input_days, self.snatcher.trade_history_df)

                if len(recent_profit_df) == 0:
                    body = f"자동거래를 통한 최근 {input_days}일 간의 손익기록이 존재하지 않습니다.\n"
                    body += f"기간을 조절하여 주시기 바랍니다."
                    self.bot.send_thread(chat_id=user_id, text=body)
                    return

                # Passed validation
                recent_profit_df = recent_profit_df.applymap(lambda x: krw(x)[:-2])
                body = f"<b>최근 {input_days}일 손익</b>"
                for row_tup in recent_profit_df.iterrows():
                    date = row_tup[0]
                    row = row_tup[1]
                    if len(row['profit_krw_after_fee']) < 11:
                        row['profit_krw_after_fee'] += ' '*(11-len(row['profit_krw_after_fee']))
                    body += f"\n{date.date()} | {row['profit_krw_after_fee']}원 | 누적 {row['profit_krw_cum']} 원"

                if detail == False:
                    self.bot.send_thread(chat_id=user_id, text=body, parse_mode=telegram.ParseMode.HTML)
                    return
                else:
                    df_columns = {
                        'addcoin_redis_uuid':'거래UUID',
                        'datetime':'거래시각',
                        'symbol':'코인심볼',
                        'dollar':'달러환율',
                        'upbit_price': '업비트 가격',
                        'upbit_qty': '업비트 수량',
                        'okx_side': 'OKX side',
                        'okx_price': 'OKX USD가격',
                        'okx_price_krw': 'OKX KRW가격',
                        'okx_liquidation_price': 'OKX 강제청산 USD가격',
                        'okx_qty': 'OKX 수량',
                        'targeted_kimp': '타겟김프',
                        'executed_kimp': '실행김프',
                        'okx_leverage': 'OKX 레버리지',
                        'upbit_pnl': '업비트 손익',
                        'upbit_fee': '업비트 수수료',
                        'okx_pnl': 'OKX 손익',
                        'okx_fee': 'OKX 수수료',
                        'profit_krw_after_fee': '수수료 적용 후 합산손익',
                        'profit_krw_after_fee_and_kimp': '수수료 및 김프 적용 후 합산손익'
                    }
                    detailed_recent_profit_df = detailed_recent_profit_df.rename(columns=df_columns).drop(['user_id','upbit_enter_krw','okx_enter','upbit_exit_krw','okx_exit','date'], axis=1)

                current_time = datetime.datetime.now()
                start_time = current_time - datetime.timedelta(days=input_days)
                save_dir = '/home/coin/excel/'
                file_name = f'Kimp_profit_history_{datetime.datetime.strftime(start_time, "%Y%m%d")}_{datetime.datetime.strftime(current_time, "%Y%m%d")}.xlsx'
                whole_dir = save_dir + file_name
                detailed_recent_profit_df.to_excel(whole_dir, index=False)
                excel_f = open(whole_dir, 'rb')
                self.bot.send_document(chat_id=user_id, document=excel_f)
                excel_f.close()
                os.remove(whole_dir)
            except Exception as e:
                body = f"서비스에 불편을 드려 죄송합니다. 일시적인 오류가 발생했습니다. 관리자에게 문의 해 주세요. (@charlie1155)\n"
                body += f"error: {e}"
                self.bot.send_thread(chat_id=user_id, text=body)
                return
        pro_thread_th = Thread(target=pro_thread, daemon=True)
        pro_thread_th.start()
    
    def his(self, update, context):
        def his_thread():
            self.get_log('his', update, context)
            user_id = update.effective_chat.id
            # Payment check
            auth = self.authorize(user_id)
            if auth is False:
                return
            try:
                input_msg = ''.join(context.args).split(',')
                if context.args == []:
                    body = f"/his 코인심볼, 최근거래내역개수 명령어를 통해 김프 자동거래내역을 조회하실 수 있습니다.\n"
                    body += f"ex) /his btc,6\n"
                    body += f"코인심볼에 all을 입력하실 경우 모든 코인에 대한 거래내역을 조회합니다.\n"
                    body += f"ex2) /his all,6\n"
                    body += f"거래내역을 엑셀파일로 다운로드 하고 싶으신 경우는 /hisf 명령어를 이용하세요."
                    self.bot.send_thread(chat_id=user_id, text=body, parse_mode=telegram.ParseMode.HTML)
                    return

                if len(input_msg) != 2:
                    body = f"잘못된 입력입니다. /his 를 입력하여 사용법을 확인 해 주세요."
                    self.bot.send_thread(chat_id=user_id, text=body)
                    return

                input_symbol = input_msg[0].upper()
                try:
                    input_number = int(input_msg[1])
                    if input_number < 1:
                        body = f"최근거래내역 개수는 양의 정수만 입력가능합니다."
                        self.bot.send_thread(chat_id=user_id, text=body)
                        return
                except:
                    body = f"최근거래내역 개수는 양의 정수만 입력가능합니다."
                    self.bot.send_thread(chat_id=user_id, text=body)
                    return

                if input_symbol not in self.get_input_symbol_list() + ['ALL']:
                    body = f"{input_symbol}은 OKX와 업비트에 동시상장되지 않은 코인입니다."
                    self.bot.send_thread(chat_id=user_id, text=body)
                    return

                # Check whether a user has correspoding trade history for a symbol
                db_client = InitDBClient(**self.local_db_dict)
                res = db_client.curr.execute("""SELECT DISTINCT symbol FROM trade_history WHERE user_id=%s""", user_id)
                if res == 0:
                    body = f"자동거래내역이 없습니다."
                    self.bot.send_thread(chat_id=user_id, text=body)
                    db_client.conn.close()
                    return
                fetched = db_client.curr.fetchall()
                db_client.conn.close()
                user_symbols = pd.DataFrame(fetched)['symbol'].to_list()
                if input_symbol not in user_symbols + ['ALL']:
                    body = f"{input_symbol}에 대한 자동거래 내역이 없습니다."
                    self.bot.send_thread(chat_id=user_id, text=body)
                    return

                # Passed all validation
                db_client = InitDBClient(**self.local_db_dict)
                if input_symbol == 'ALL':
                    sql = """SELECT * FROM trade_history WHERE user_id=%s"""
                    val = user_id
                else:
                    sql = """SELECT * FROM trade_history WHERE symbol=%s AND user_id=%s"""
                    val = (input_symbol, user_id)
                db_client.curr.execute(sql, val)
                trade_history_df = pd.DataFrame(db_client.curr.fetchall())
                db_client.conn.close()
                trade_history_df = trade_history_df.sort_values('datetime', ascending=False).head(input_number).reset_index(drop=True)
                
                body = "<b>자동거래 내역</b>"
                for row_tup in trade_history_df.iterrows():
                    index = row_tup[0]
                    row = row_tup[1]
                    datetime_kst = row['datetime']
                    symbol = row['symbol']
                    dollar = row['dollar']
                    try:
                        addcoin_redis_uuid = row['addcoin_redis_uuid']
                    except:
                        addcoin_redis_uuid = "없음"
                    if row['upbit_side'] == 'bid':
                        kimp_side = '진입'
                        upbit_side = '매수'
                        okx_side = '숏'
                    else:
                        kimp_side = '탈출'
                        upbit_side = '매도'
                        okx_side = '롱'
                    upbit_price = row['upbit_price']
                    upbit_qty = row['upbit_qty']
                    okx_price = row['okx_price']
                    okx_qty = row['okx_qty']
                    targeted_kimp = row['targeted_kimp']
                    executed_kimp = row['executed_kimp']
                    body += f"\n\n<b>거래UUID: {addcoin_redis_uuid}|{symbol} {kimp_side}</b>|{datetime_kst}|달러: {dollar}\n업비트{upbit_side}: {upbit_price}원, {upbit_qty}개|OKX{okx_side}: {okx_price}USD, {okx_qty}개\n"
                    body += f"업비트거래금액: {krw(round(upbit_price*upbit_qty))}원|OKX 레버리지: {row['okx_leverage']}배\n"
                    body += f"<b>타겟김프: {round(targeted_kimp*100,3)}%</b>, <b>실행김프: {round(executed_kimp*100,3)}%</b>\n"
                    body += f"<b>타겟테더: {round(dollar*(1+targeted_kimp),2)}원</b>, <b>실행테더: {round(dollar*(1+executed_kimp),2)}원</b>"
                self.bot.send_thread(chat_id=user_id, text=body, parse_mode=telegram.ParseMode.HTML)
                return
            except Exception as e:
                self.telegram_bot_logger.error(f"his|{traceback.format_exc()}")
                body = f"서비스에 불편을 드려 죄송합니다. 일시적인 오류가 발생했습니다. 관리자에게 문의 해 주세요. (@charlie1155)\n"
                body += f"error: {e}"
                self.bot.send_thread(chat_id=user_id, text=body)
                return
        his_thread_th = Thread(target=his_thread, daemon=True)
        his_thread_th.start()
    
    def hisf(self, update, context):
        def hisf_thread():
            self.get_log('hisf', update, context)
            user_id = update.effective_chat.id
            # Payment check
            auth = self.authorize(user_id)
            if auth is False:
                return
            try:
                input_msg = ''.join(context.args).split(',')
                if context.args == []:
                    body = f"/hisf 코인심볼, 최근거래내역개수 명령어를 통해 김프 자동거래내역을 엑셀파일로 다운로드 하실 수 있습니다.\n"
                    body += f"ex) /hisf btc,6\n"
                    body += f"코인심볼에 all을 입력하실 경우 모든 코인에 대한 거래내역을 가져옵니다.\n"
                    body += f"ex2) /hisf all,6\n"
                    self.bot.send_thread(chat_id=user_id, text=body, parse_mode=telegram.ParseMode.HTML)
                    return

                if len(input_msg) != 2:
                    body = f"잘못된 입력입니다. /hisf 를 입력하여 사용법을 확인 해 주세요."
                    self.bot.send_thread(chat_id=user_id, text=body)
                    return

                input_symbol = input_msg[0].upper()
                try:
                    input_number = int(input_msg[1])
                    if input_number < 1:
                        body = f"최근거래내역 개수는 양의 정수만 입력가능합니다."
                        self.bot.send_thread(chat_id=user_id, text=body)
                        return
                except:
                    body = f"최근거래내역 개수는 양의 정수만 입력가능합니다."
                    self.bot.send_thread(chat_id=user_id, text=body)
                    return

                if input_symbol not in self.get_input_symbol_list() + ['ALL']:
                    body = f"{input_symbol}은 OKX와 업비트에 동시상장되지 않은 코인입니다."
                    self.bot.send_thread(chat_id=user_id, text=body)
                    return

                # Check whether a user has correspoding trade history for a symbol
                db_client = InitDBClient(**self.local_db_dict)
                res = db_client.curr.execute("""SELECT DISTINCT symbol FROM trade_history WHERE user_id=%s""", user_id)
                if res == 0:
                    body = f"자동거래내역이 없습니다."
                    self.bot.send_thread(chat_id=user_id, text=body)
                    db_client.conn.close()
                    return
                fetched = db_client.curr.fetchall()
                db_client.conn.close()
                user_symbols = pd.DataFrame(fetched)['symbol'].to_list()
                if input_symbol not in user_symbols + ['ALL']:
                    body = f"{input_symbol}에 대한 자동거래 내역이 없습니다."
                    self.bot.send_thread(chat_id=user_id, text=body)
                    return

                # Passed all validation
                body = f'데이터를 추출 중입니다. 잠시만 기다려 주세요..'
                self.bot.send_thread(chat_id=user_id, text=body)

                db_client = InitDBClient(**self.local_db_dict)
                if input_symbol == 'ALL':
                    sql = """SELECT * FROM trade_history WHERE user_id=%s"""
                    val = user_id
                else:
                    sql = """SELECT * FROM trade_history WHERE symbol=%s AND user_id=%s"""
                    val = (input_symbol, user_id)
                db_client.curr.execute(sql, val)
                trade_history_df = pd.DataFrame(db_client.curr.fetchall()).drop('id', axis=1)
                db_client.conn.close()
                trade_history_df = trade_history_df.where(trade_history_df.notnull(), None)
                trade_history_df = trade_history_df.drop(['user_id','remark'], axis=1).sort_values('datetime', ascending=False).head(input_number).reset_index(drop=True)
                trade_history_df.loc[:,'addcoin_redis_uuid'] = trade_history_df['addcoin_redis_uuid'].apply(lambda x: x if x!=None else '없음')
                trade_history_df['김프거래방향'] = trade_history_df['upbit_side'].apply(lambda x: '진입' if x == 'bid' else '탈출')
                trade_history_df['업비트 거래금액'] = trade_history_df['upbit_price'] * trade_history_df['upbit_qty']
                trade_history_df['OKX USD거래금액'] = trade_history_df['okx_price'] * trade_history_df['okx_qty']
                trade_history_df['OKX KRW거래금액'] = trade_history_df['okx_price_krw'] * trade_history_df['okx_qty']
                trade_history_df['타겟테더환산가'] = trade_history_df['dollar'] * (1+trade_history_df['targeted_kimp'])
                trade_history_df['실행테더환산가'] = trade_history_df['dollar'] * (1+trade_history_df['executed_kimp'])

                trade_history_df = trade_history_df.rename(columns={
                    'addcoin_redis_uuid': '거래UUID',
                    'datetime':'거래시각',
                    'symbol':'코인심볼',
                    'dollar':'달러환율',
                    'upbit_side': '업비트 side',
                    'upbit_price': '업비트 가격',
                    'upbit_qty': '업비트 수량',
                    'okx_side': 'OKX side',
                    'okx_price': 'OKX USD가격',
                    'okx_price_krw': 'OKX KRW가격',
                    'okx_liquidation_price': 'OKX 강제청산 USD가격',
                    'okx_qty': 'OKX 수량',
                    'targeted_kimp': '타겟김프',
                    'executed_kimp': '실행김프',
                    'okx_leverage': 'OKX 레버리지',
                })
                trade_history_df = (trade_history_df[['거래UUID','거래시각','코인심볼','달러환율','김프거래방향','업비트 side','업비트 가격','업비트 수량','업비트 거래금액', 'OKX 레버리지',
                'OKX side','OKX USD가격','OKX KRW가격','OKX 강제청산 USD가격','OKX 수량','OKX USD거래금액','OKX KRW거래금액','타겟김프','실행김프',
                '타겟테더환산가','실행테더환산가','upbit_uuid','okx_orderId']])

                save_dir = '/home/coin/excel/'
                file_name = f'{input_symbol}_Kimp_trading_history_{len(trade_history_df)}_{user_id}.xlsx'
                whole_dir = save_dir + file_name
                trade_history_df.to_excel(whole_dir, index=False)
                excel_f = open(whole_dir, 'rb')
                body = f"조회된 거래내역 수: {len(trade_history_df)}개\n"
                self.bot.send_document(chat_id=user_id, document=excel_f)
                excel_f.close()
                os.remove(whole_dir)
                
            except Exception as e:
                body = f"서비스에 불편을 드려 죄송합니다. 일시적인 오류가 발생했습니다. 관리자에게 문의 해 주세요. (@charlie1155)\n"
                body += f"error: {e}"
                self.bot.send_thread(chat_id=user_id, text=body)
                return
        hisf_thread_th = Thread(target=hisf_thread, daemon=True)
        hisf_thread_th.start()
    
    def cgh(self, update, context):
        def cgh_thread():
            self.get_log('cgh', update, context)
            user_id = update.effective_chat.id
            # Payment check
            auth = self.authorize(user_id)
            if auth is False:
                return
            try:
                input_msg = ''.join(context.args).split(',')
                if context.args == []:
                    body = f"/cgh 명령어로 /addcoin 의 자동매매기능으로 <b>이미 진입되어있는 코인의 탈출가격을 변경</b>할 수 있습니다.\n"
                    body += f"/cgh 거래ID(/addcoin 에서 확인가능), 새로운탈출김프 형식으로 입력 해 주세요.\n"
                    body += f"ex) /cgh 1753,3\n"
                    body += f"/addcoin 이 아닌, 수동으로 진입한 포지션에 대해서는 영향을 미치지 않으며, 현재 탈출대기 중이 아닌 코인에 대해서는 사용할 수 없습니다.\n"
                    body += f"탈출대기 중이 아닌 코인은 /rmcoin 으로 삭제 후 재등록 바랍니다."
                    self.bot.send_thread(chat_id=user_id, text=body, parse_mode=telegram.ParseMode.HTML)
                    return

                if len(input_msg) != 2:
                    body = f"잘못된 입력입니다. /cgh 로 사용법을 확인하세요."
                    self.bot.send_thread(chat_id=user_id, text=body)
                    return
            
                try:
                    input_addcoin_display_id = int(input_msg[0])
                    input_addcoin_redis_uuid = display_id_to_redis_uuid(user_id, self.snatcher.addcoin_df, input_addcoin_display_id)
                except:
                    body = f"거래ID 는 숫자만 입력이 가능합니다. /cgh 를 입력하여 사용법을 확인하세요."
                    self.bot.send_thread(chat_id=user_id, text=body)
                    return
                
                try:
                    input_high = float(input_msg[1])
                except:
                    body = f"탈출김프 혹은 탈출 USDT환산가는 숫자만 입력이 가능합니다.\n"
                    body += f"/cgh 를 입력하여 사용법을 확인하세요."
                    self.bot.send_thread(chat_id=user_id, text=body)
                    return

                user_waiting_coin_df = self.snatcher.addcoin_df[(self.snatcher.addcoin_df['user_id']==user_id)&(self.snatcher.addcoin_df['auto_trade_switch']==-1)]
                if input_addcoin_redis_uuid not in user_waiting_coin_df['redis_uuid'].to_list():
                    body = f"거래ID: {input_addcoin_display_id} 은 /addcoin 자동매매 기능으로 진입되어있는 상태가 아니므로 탈출김프 혹은 탈출USDT환산가를 변경할 수 없습니다.\n"
                    body += f"/cgh 명령어는 자동매매 기능으로 김프거래에 진입되어 있는 코인에만 사용이 가능합니다.\n"
                    self.bot.send_thread(chat_id=user_id, text=body)
                    return

                user_low_value = user_waiting_coin_df[user_waiting_coin_df['redis_uuid']==input_addcoin_redis_uuid]['low'].values[0]
                symbol = user_waiting_coin_df[user_waiting_coin_df['redis_uuid']==input_addcoin_redis_uuid]['symbol'].values[0]
                if input_high <= user_low_value:
                    body = f"입력된 수정 High 값({input_high})이 최초설정된 Low 값({user_low_value})보다 작거나 같습니다.\n"
                    body += f"김프거래 즉시 정리는 /exit 명령어를 이용하시기 바랍니다.\n"
                    body += f"High 값 변경을 취소합니다."
                    self.bot.send_thread(chat_id=user_id, text=body)
                    return

                # passed all validation
                # update database
                db_client = InitDBClient(**self.local_db_dict)
                db_client.curr.execute("""SELECT high FROM addcoin WHERE redis_uuid=%s""", input_addcoin_redis_uuid)
                before_high = db_client.curr.fetchall()[0]['high']
                db_client.curr.execute("""UPDATE addcoin SET last_updated_timestamp=%s, high=%s WHERE redis_uuid=%s""", (datetime.datetime.now().timestamp()*10000000, input_high, input_addcoin_redis_uuid))
                db_client.conn.commit()
                db_client.conn.close()

                body = f"거래ID:{input_addcoin_display_id}({symbol})의 탈출김프 혹은 탈출USDT환산가가\n"
                body += f"{before_high}에서 <b>{input_high}</b>로 변경되었습니다."
                self.bot.send_thread(chat_id=user_id, text=body, parse_mode=telegram.ParseMode.HTML)
                return
            except Exception as e:
                    body = f"서비스에 불편을 드려 죄송합니다. 일시적인 오류가 발생했습니다. 관리자에게 문의 해 주세요. (@charlie1155)\n"
                    body += f"error: {e}"
                    self.bot.send_thread(chat_id=user_id, text=body)
                    return
        cgh_thread_th = Thread(target=cgh_thread, daemon=True)
        cgh_thread_th.start()
    
    def plot(self, update, context):
        def plot_thread():
            self.get_log('plot', update, context)
            # Payment check
            user_id = update.effective_chat.id
            auth = self.authorize(user_id)
            if auth is False:
                return
            try:
                input_msg = ''.join(context.args).split(',')
                if 'detail' in input_msg:
                    detail = True
                    input_msg = [x for x in input_msg if x != 'detail']
                else:
                    detail = False
                if 'kp' in input_msg:
                    compare_usdt_kp = True
                    input_msg = [x for x in input_msg if x != 'kp']
                else:
                    compare_usdt_kp = False
                if len(input_msg) < 2:
                    body = f'검색할 코인심볼과 캔들종류를 순서대로 ,로 분리하여 입력하세요.'
                    body += f'\n얇은 선은 볼린저 밴드를 나타내며, 녹색 점선은 선형회귀선입니다.'
                    body += f'\n업비트와 OKX USDT선물시장에 동시상장된 코인들만 검색이 가능하며 동시에 여러코인을 차트로 그릴 수 있습니다.'
                    body += f'\n김프차트를 캔들스틱 차트로 나타내고 싶으시면 /plotc 명령어를 이용해 주세요.'
                    body += f'\n캔들(봉) 종류는 1(1분), 5(5분), 30(30분), 60(1시간), 240(4시간), days(1일), weeks(1주일) 입니다.'
                    body += f'\n사용예시1) /plot btc,5'
                    body += f'\n사용예시2) /plot btc,xrp,eth,5'
                    body += f'\n사용예시3) /plot btc,xrp,days'
                    body += f"\n차트를 확대하려면 명령어 끝에 'detail' 을 추가하세요."
                    body += f'\n사용예시4) /plot btc,1,detail'
                    body += f"\n테더환산가와 김프를 동시에 보시려면 명령어 끝에 'kp'를 추가하세요."
                    body += f"\n사용예시5) /Plot btc,1,kp"
                    self.bot.send_thread(chat_id=user_id, text=body)
                    return

                input_symbol_list = input_msg[:-1]
                input_symbol_list = [x.upper() for x in input_symbol_list]
                coin_list = self.get_input_symbol_list()

                # If symbol input is wrong
                if input_symbol_list != [x for x in input_symbol_list if x in coin_list]:
                    body = f'코인심볼명에 오류가 있습니다.'
                    body += f'\n올바른 사용방법은 /plot 을 입력하여 확인해주세요.'
                    self.bot.send_thread(chat_id=user_id, text=body)
                    return
                # If candle input is wrong
                if input_msg[-1] in ['1','5','30','60','240']:
                    period = int(input_msg[-1])
                elif input_msg[-1] in ['days','weeks']:
                    period = input_msg[-1]
                else:
                    # Handle error
                    body = f'조회 가능한 분봉 목록은 다음과 같습니다.'
                    body += f'\n1(1분), 5(5분), 30, 60, 240, days(일), weeks(주)'
                    body += f'\n사용예시1) /plot btc,1'
                    body += f'\n사용예시2) /plot btc,eth,days'
                    self.bot.send_thread(chat_id=user_id, text=body)
                    return
                self.bot.send_thread(chat_id=user_id, text=f'차트데이터를 추출 중입니다..\n')
                start = time.time()
                # use multiprocessing for drawing a plot
                manager = Manager()
                return_dict = manager.dict()
                get_plot_proc = Process(target=self.data_processor.get_plot, args=(input_symbol_list, period, detail, compare_usdt_kp, 9, return_dict), daemon=True)
                get_plot_proc.start()
                get_plot_proc.join()
                buf = return_dict['return']
                fetch_time = time.time() - start
                self.bot.send_thread(chat_id=user_id, text=f'차트를 전송 중입니다. 잠시만 기다려 주세요..\n(Fetch time: {round(fetch_time,2)}s)')
                buf.seek(0)
                self.bot.send_photo(chat_id=user_id, photo=buf)
                buf.close()
            except Exception as e:
                self.telegram_bot_logger.error(f"plot|{traceback.format_exc()}")
                body = f"서비스에 불편을 드려 죄송합니다. 일시적인 오류가 발생했습니다. 관리자에게 문의 해 주세요. (@charlie1155)\n"
                body += f"error: {e}"
                self.bot.send_thread(chat_id=user_id, text=body)
                return
        plot_thread_th = Thread(target=plot_thread, daemon=True)
        plot_thread_th.start()
    
    def plotc(self, update, context):
        def plotc_thread():
            self.get_log('plotc', update, context)
            # Payment check
            user_id = update.effective_chat.id
            auth = self.authorize(user_id)
            if auth is False:
                return
            try:
                input_msg = ''.join(context.args).split(',')
                if 'detail' in input_msg:
                    detail = True
                    input_msg = [x for x in input_msg if x != 'detail']
                else:
                    detail = False

                if context.args == []:
                    body = f'/plotc 명령어는 업비트와 OKX USD-M 선물 간의 김프차트를 시가, 고가, 저가, 종가를 반영하는 캔들차트로 나타내는 명령어입니다.'
                    body += f'\n검색할 코인심볼, 캔들종류를 순서대로 ,로 분리하여 입력하세요.'
                    body += f'\n얇은 선은 볼린저 밴드를 나타내며, 녹색 점선은 선형회귀선입니다.'
                    body += f'\n업비트와 OKX 선물시장에 동시상장된 코인들만 검색이 가능하며 한 번에 하나의 코인만 검색 할 수 있습니다.'
                    body += f'\n캔들(봉) 종류는 1(1분), 5(5분), 30(30분), 60(1시간), 240(4시간), days(1일), weeks(1주일) 입니다.'
                    body += f'\n사용예시1) /plotc btc,5'
                    body += f'\n사용예시2) /plotc xrp,5'
                    body += f'\n사용예시3) /plotc xrp,days'
                    body += f"\n차트를 확대하려면 명령어 끝에 'detail' 을 추가하세요."
                    body += f'\n사용예시4) /plotc btc,1,detail'
                    self.bot.send_thread(chat_id=user_id, text=body)
                    return

                if len(input_msg) != 2:
                    body = f"잘못된 입력입니다.\n"
                    body += f"/plotc 를 입력하여 사용법을 확인해 주세요."
                    self.bot.send_thread(chat_id=user_id, text=body)
                    return

                coin = input_msg[0].upper()
                # If coin symbol is wrong
                if coin not in self.get_input_symbol_list():
                    body = f'{coin}은 업비트와 바이비트에 동시상장되지 않은 코인입니다.\n'
                    body += f'/plotc 를 입력해서 사용법을 확인 해 주세요.'
                    self.bot.send_thread(chat_id=user_id, text=body)
                    return
                # If candle input is wrong
                if input_msg[-1] in ['1','5','30','60','240']:
                    period = int(input_msg[-1])
                elif input_msg[-1] in ['days','weeks']:
                    period = input_msg[-1]
                else:
                    # Handle error
                    body = f'조회 가능한 분봉 목록은 다음과 같습니다.'
                    body += f'\n1(1분), 5(5분), 30, 60, 240, days(일), weeks(주)'
                    body += f'\n사용예시1) /plot btc,eth,5'
                    body += f'\n사용예시2) /plot btc,days'
                    self.bot.send_thread(chat_id=user_id, text=body)
                    return
                self.bot.send_thread(chat_id=user_id, text=f'차트데이터를 추출 중입니다..\n')
                start = time.time()
                # use multiprocessing for drawing a plot
                manager = Manager()
                return_dict = manager.dict()
                get_plotc_proc = Process(target=self.data_processor.get_plotc, args=(coin, period, detail, 9, return_dict), daemon=True)
                get_plotc_proc.start()
                get_plotc_proc.join()
                buf = return_dict['return']
                # buf = get_plotc(coin, period, detail)
                fetch_time = time.time() - start
                self.bot.send_thread(chat_id=user_id, text=f'차트를 전송 중입니다. 잠시만 기다려 주세요..\n(Fetch time: {round(fetch_time,2)}s)')
                buf.seek(0)
                self.bot.send_photo(chat_id=user_id, photo=buf)
                buf.close()
                # os.remove(whole_dir)
            except Exception as e:
                self.telegram_bot_logger.error(f"plotc|{traceback.format_exc()}")
                body = f"서비스에 불편을 드려 죄송합니다. 일시적인 오류가 발생했습니다. 관리자에게 문의 해 주세요. (@charlie1155)\n"
                body += f"error: {e}"
                self.bot.send_thread(chat_id=user_id, text=body)
                return
        plotc_thread_th = Thread(target=plotc_thread, daemon=True)
        plotc_thread_th.start()
    
    def enter(self, update, context):
        def enter_thread():
            self.get_log('enter', update, context)
            user_id = update.effective_chat.id
            # Payment check
            auth = self.authorize(user_id)
            if auth is False:
                return
            try:
                input_msg = ''.join(context.args).split(',')
                dollar = self.get_dollar_dict()['price']
                user_okx_leverage = int(self.snatcher.userinfo_df[self.snatcher.userinfo_df['user_id']==user_id]['okx_leverage'].values[0])
                user_okx_cross = int(self.snatcher.userinfo_df[self.snatcher.userinfo_df['user_id']==user_id]['okx_cross'].values[0])
                if context.args == []:
                    body = f"/enter 는 수동으로 김프거래에 진입하는 명령어입니다.\n"
                    body += f"/enter 심볼명, 투입자본(원) 를 입력하시면,\n업비트 현물매수, OKX USDT선물공매도가 동시에 자동진행됩니다.\n"
                    body += f"ex) /enter xrp,100000\n"
                    body += f"동일한 코인 개수를 기준으로 양방 진입하게 되며, 업비트와 OKX의 코인개수를 정확하게 동일하게 맞추기 위해,\n"
                    body += f"입력한 투입자본을 넘지않는 선에서 투입금액이 자동 조정됩니다.\n"
                    body += f"OKX 레버리지는 /lev 로 설정된 레버리지로 변경되며, 격리마진으로 설정됩니다.\n"
                    body += f"업비트와 OKX 선물지갑에 잔고가 부족하면 거래가 실행되지 않습니다."
                    self.bot.send_thread(chat_id=user_id, text=body)
                    return
                
                if len(input_msg) != 2:
                    body = f"잘못된 입력입니다. /enter 를 입력하여 사용법을 확인해 주세요."
                    self.bot.send_thread(chat_id=user_id, text=body)
                    return
                
                symbol = input_msg[0].upper()
                try:
                    value_krw = float(input_msg[1])
                except:
                    body = f"투입자본(원)은 숫자만 입력가능합니다."
                    self.bot.send_thread(chat_id=user_id, text=body)
                    return
                
                if symbol not in [x.replace('-USDT-SWAP', '') for x in self.get_both_listed_okx_symbols()]:
                    body = f"{symbol}은 업비트와 OKX USDT 선물시장에 동시상장된 코인이 아닙니다."
                    self.bot.send_thread(chat_id=user_id, text=body)
                    return
                if value_krw <= 5*dollar:
                    body = f"주문은 5USDT 이상부터 가능합니다."
                    self.bot.send_thread(chat_id=user_id, text=body)
                    return
                
                # Load API Keys
                try:
                    user_upbit_access_key, user_upbit_secret_key = self.snatcher.user_api_key_df[(self.snatcher.user_api_key_df['user_id']==user_id)&(self.snatcher.user_api_key_df['exchange']=='UPBIT')]\
                    .sample(n=1)[['access_key', 'secret_key']].values[0]
                    user_okx_access_key, user_okx_secret_key, user_okx_passphrase = self.snatcher.user_api_key_df[(self.snatcher.user_api_key_df['user_id']==user_id)&(self.snatcher.user_api_key_df['exchange']=='OKX')]\
                    .sample(n=1)[['access_key', 'secret_key', 'passphrase']].values[0]
                except Exception:
                    body = f"등록된 API 키가 없어 거래소와 통신이 불가능합니다.\n"
                    body += f"/api_key 명령어를 이용하여 업비트와 OKX의 API 키를 등록해 주세요."
                    self.bot.send_thread(chat_id=user_id, text=body)
                    return

                # Passed validation process.
                # Proceed investment
                # Fetch user API keys
                kimp_df = self.get_kimp_df()
                self.snatcher.enter_func(kimp_df, dollar, user_id, None, symbol, value_krw, user_upbit_access_key, user_upbit_secret_key, user_okx_access_key, user_okx_secret_key, user_okx_passphrase, user_okx_leverage, user_okx_cross)
                return
            except Exception as e:
                self.telegram_bot_logger.error(f"enter|{traceback.format_exc()}")
                body = f"서비스에 불편을 드려 죄송합니다. 일시적인 오류가 발생했습니다. 관리자에게 문의 해 주세요. (@charlie1155)\n"
                body += f"error: {e}"
                self.bot.send_thread(chat_id=user_id, text=body)
                return
        enter_thread_th = Thread(target=enter_thread, daemon=True)
        enter_thread_th.start()
    
    def exit(self, update, context):
        def exit_thread():
            self.get_log('exit', update, context)
            user_id = update.effective_chat.id
            # Payment check
            auth = self.authorize(user_id)
            if auth is False:
                return
            try:
                input_msg = ''.join(context.args).split(',')
                if context.args == []:
                    body = f"/exit 은 김프거래를 수동으로 정리하는 명령어입니다.\n"
                    body += f"/exit 심볼명, 정리코인개수 를 입력하시면,\n업비트 현물매도, OKX USDT선물공매수(숏정리)가 동시에 자동진행됩니다.\n"
                    body += f"ex) /exit xrp,30\n"
                    body += f"코인개수를 별도로 입력하지 않으면, 업비트와 OKX 양측에 보유한 모든 포지션을 정리합니다.\n"
                    body += f"ex) /exit xrp\n"
                    body += f"<b>주의!</b>: /addcoin 에 자동거래로 이미 진입되어 있는 코인을 /exit 을 통해 수동으로 정리하면,\n"
                    body += f"전량을 정리할 경우(수량 미지정 시) 해당 코인의 /addcoin 자동거래의 탈출이 자동으로 비활성화 됩니다.\n"
                    body += f"또한, 전량 정리 시에는, 업비트에 보유하고 있는 모든 잔량을 매도하기 때문에, <b>기존에 보유하고 있는 물량이 매도</b>되므로 주의하시기 바랍니다.\n"
                    body += f"/addcoin 를 통해 김프거래에 진입되어있는 코인을 탈출하시려는 경우는, /exita 명령어를 활용하여 정리하세요."
                    self.bot.send_thread(chat_id=user_id, text=body, parse_mode=telegram.ParseMode.HTML)
                    return
                
                if len(input_msg) > 2:
                    body = f"잘못된 입력입니다. /enter 를 입력하여 사용법을 확인해 주세요."
                    self.bot.send_thread(chat_id=user_id, text=body)
                    return

                if len(input_msg) == 1:
                    symbol = input_msg[0].upper()
                    if symbol not in [x.replace('-USDT-SWAP', '') for x in self.get_both_listed_okx_symbols()]:
                        body = f"{symbol}은 업비트와 OKX USDT 선물시장에 동시상장된 코인이 아닙니다."
                        self.bot.send_thread(chat_id=user_id, text=body)
                        return
                    exit_qty = None
                else:
                    symbol = input_msg[0].upper()
                    if symbol not in [x.replace('-USDT-SWAP', '') for x in self.get_both_listed_okx_symbols()]:
                        body = f"{symbol}은 업비트와 OKX USDT 선물시장에 동시상장된 코인이 아닙니다."
                        self.bot.send_thread(chat_id=user_id, text=body)
                        return
                    try:
                        exit_qty = float(input_msg[1])
                    except:
                        body = f"코인수량은 숫자만 입력가능합니다."
                        self.bot.send_thread(chat_id=user_id, text=body)
                        return
                
                # Load API Keys
                try:
                    user_upbit_access_key, user_upbit_secret_key = self.snatcher.user_api_key_df[(self.snatcher.user_api_key_df['user_id']==user_id)&(self.snatcher.user_api_key_df['exchange']=='UPBIT')]\
                    .sample(n=1)[['access_key', 'secret_key']].values[0]
                    user_okx_access_key, user_okx_secret_key, user_okx_passphrase = self.snatcher.user_api_key_df[(self.snatcher.user_api_key_df['user_id']==user_id)&(self.snatcher.user_api_key_df['exchange']=='OKX')]\
                    .sample(n=1)[['access_key', 'secret_key', 'passphrase']].values[0]
                except Exception:
                    body = f"등록된 API 키가 없어 거래소와 통신이 불가능합니다.\n"
                    body += f"/api_key 명령어를 이용하여 업비트와 OKX의 API 키를 등록해 주세요."
                    self.bot.send_thread(chat_id=user_id, text=body)
                    return

                # Passed all validation
                # if there's registered addcoin change auto_trade_switch to 1 in the case of exiting all position // 1 = 탈출완료
                user_addcoin_df = self.snatcher.addcoin_df[self.snatcher.addcoin_df['user_id']==user_id]
                user_okx_cross = int(self.snatcher.userinfo_df[self.snatcher.userinfo_df['user_id']==user_id]['okx_cross'].values[0])
                if user_okx_cross == 0:
                    user_mgnMode = 'isolated'
                else:
                    user_mgnMode = 'cross'
                registered_alarm_coin_df = user_addcoin_df[user_addcoin_df['symbol'].str.contains(symbol)]
                if len(registered_alarm_coin_df) != 0 and exit_qty == None:
                    db_client = InitDBClient(**self.local_db_dict)
                    for row_tup in registered_alarm_coin_df.iterrows():
                        row = row_tup[1]
                        if row['auto_trade_capital'] == None:
                            continue
                        db_client.curr.execute("""UPDATE addcoin SET last_updated_timestamp=%s, auto_trade_switch=%s WHERE user_id=%s AND symbol=%s""", (datetime.datetime.now().timestamp()*10000000, 1, row['user_id'], row['symbol']))
                    db_client.conn.commit()
                    db_client.conn.close()

                # Start trades
                dollar = self.get_dollar_dict()['price']
                kimp_df = self.get_kimp_df()

                if exit_qty != None:
                    exit_qty = (exit_qty, exit_qty)
                self.snatcher.exit_func(kimp_df, dollar, user_id, None, user_mgnMode, symbol, exit_qty, user_upbit_access_key, user_upbit_secret_key, user_okx_access_key, user_okx_secret_key, user_okx_passphrase)
                return
            except Exception as e:
                self.telegram_bot_logger.error(f"exit|{traceback.format_exc()}")
                body = f"서비스에 불편을 드려 죄송합니다. 일시적인 오류가 발생했습니다. 관리자에게 문의 해 주세요. (@charlie1155)\n"
                body += f"error: {e}"
                self.bot.send_thread(chat_id=user_id, text=body)
                return
        exit_thread_th = Thread(target=exit_thread, daemon=True)
        exit_thread_th.start()

    def exita(self, update, context):
        def exita_thread():
            self.get_log('exita', update, context)
            user_id = update.effective_chat.id
            # Payment check
            auth = self.authorize(user_id)
            if auth is False:
                return
            try:
                input_msg = ''.join(context.args).split(',')
                if context.args == []:
                    body = f"/exita 은 자동(addcoin 자동거래)으로 진입되어있는 김프거래를 정리하는 명령어입니다.\n"
                    body += f"/exita 거래ID 를 입력하시면,\n해당 거래ID의 김프거래가 정리됩니다.\n"
                    body += f"거래ID 는 /addcoin 을 통해 확인하실 수 있습니다.\n"
                    body += f"ex) /exita 16\n"
                    body += f"콤마를 사용하여, 동시에 여러 거래를 정리할 수 있습니다.\n"
                    body += f"ex) /exita 16,17,18"
                    self.bot.send_thread(chat_id=user_id, text=body)
                    return
                
                try:
                    input_display_id_list = [int(x) for x in input_msg]
                    input_redis_uuid_list = [display_id_to_redis_uuid(user_id, self.snatcher.addcoin_df, x) for x in input_display_id_list]
                except:
                    body = f"거래ID는 숫자만 입력가능합니다."
                    self.bot.send_thread(chat_id=user_id, text=body)
                    return

                user_waiting_coin_df = self.snatcher.addcoin_df[(self.snatcher.addcoin_df['user_id']==user_id)&(self.snatcher.addcoin_df['auto_trade_switch']==-1)]
                user_waiting_coin_id_list = user_waiting_coin_df['redis_uuid'].to_list()
                user_okx_cross = int(self.snatcher.userinfo_df[self.snatcher.userinfo_df['user_id']==user_id]['okx_cross'].values[0])
                if user_okx_cross == 0:
                    user_mgnMode = 'isolated'
                else:
                    user_mgnMode = 'cross'

                not_in_list = [x for x in input_redis_uuid_list if x not in user_waiting_coin_id_list]
                if len(not_in_list) != 0:
                    body = f"{','.join([str(x) for x in not_in_list])}은 김프거래에 진입되어 있지 않은 거래ID 입니다.\n"
                    body += f"/addcoin 을 입력하여 다시 한 번 확인 해 주세요."
                    self.bot.send_thread(chat_id=user_id, text=body)
                    return
                
                # Load API Keys
                try:
                    user_upbit_access_key, user_upbit_secret_key = self.snatcher.user_api_key_df[(self.snatcher.user_api_key_df['user_id']==user_id)&(self.snatcher.user_api_key_df['exchange']=='UPBIT')]\
                    .sample(n=1)[['access_key', 'secret_key']].values[0]
                    user_okx_access_key, user_okx_secret_key, user_okx_passphrase = self.snatcher.user_api_key_df[(self.snatcher.user_api_key_df['user_id']==user_id)&(self.snatcher.user_api_key_df['exchange']=='OKX')]\
                    .sample(n=1)[['access_key', 'secret_key', 'passphrase']].values[0]
                except Exception:
                    body = f"등록된 API 키가 없어 거래소와 통신이 불가능합니다.\n"
                    body += f"/api_key 명령어를 이용하여 업비트와 OKX의 API 키를 등록해 주세요."
                    self.bot.send_thread(chat_id=user_id, text=body)
                    return

                # Passed all validation
                db_clinet = InitDBClient(**self.local_db_dict)
                for redis_uuid in input_redis_uuid_list:
                    user_alarm_coin_df = self.snatcher.addcoin_df[self.snatcher.addcoin_df['redis_uuid']==redis_uuid]
                    enter_upbit_uuid = user_alarm_coin_df['enter_upbit_uuid'].values[0]
                    symbol = user_alarm_coin_df['symbol'].values[0]
                    symbol = symbol.replace('USDT', '')

                    exit_id_list = [] # for updating upbit uuid and okx orderId
                    upbit_exit_qty = self.snatcher.trade_history_df[self.snatcher.trade_history_df['upbit_uuid']==enter_upbit_uuid]['upbit_qty'].values[0]
                    okx_exit_qty = self.snatcher.trade_history_df[self.snatcher.trade_history_df['upbit_uuid']==enter_upbit_uuid]['okx_qty'].values[0]
                    
                    kimp_df = self.get_kimp_df()
                    self.snatcher.exit_func(kimp_df, self.get_dollar_dict()['price'], user_id, redis_uuid, user_mgnMode, symbol, (upbit_exit_qty,okx_exit_qty), user_upbit_access_key, user_upbit_secret_key, user_okx_access_key, user_okx_secret_key, user_okx_passphrase, exit_id_list)
                    self.snatcher.exec_pnl(kimp_df, user_id, redis_uuid, exit_id_list[0], self.get_dollar_dict()['price'])
                    # UPDATE database
                    timestamp_now = datetime.datetime.now().timestamp()*10000000
                    switch = 1
                    auto_trade_switch = 1
                    db_clinet.curr.execute("""UPDATE addcoin SET last_updated_timestamp=%s, switch=%s, auto_trade_switch=%s, exit_upbit_uuid=%s, exit_okx_orderId=%s WHERE redis_uuid=%s""", (timestamp_now, switch, auto_trade_switch, exit_id_list[0], exit_id_list[1], redis_uuid))
                    db_clinet.conn.commit()
                db_clinet.conn.close()
                return
            except Exception as e:
                self.telegram_bot_logger.error(f'exita|{traceback.format_exc()}')
                body = f"서비스에 불편을 드려 죄송합니다. 일시적인 오류가 발생했습니다. 관리자에게 문의 해 주세요. (@charlie1155)\n"
                body += f"error: {e}"
                self.bot.send_thread(chat_id=user_id, text=body)
                return
        exita_thread_th = Thread(target=exita_thread, daemon=True)
        exita_thread_th.start()
    
    def std(self, update, context):
        def std_thread():
            self.get_log('std', update, context)
            user_id = update.effective_chat.id
            # Payment check
            auth = self.authorize(user_id)
            if auth is False:
                return
            try:
                input_msg = ''.join(context.args).split(',')
                if context.args == []:
                    body = f"각 코인별 최근 n일 간의 김프 변동성을 구하는 명령어입니다.\n"
                    body += f"각 종목별 과거 1분봉 종가의 표준편차를 변동성으로 간주하며,\n"
                    body += f"표준편차가 높은 순(변동성이 높은 순)으로 나열됩니다.\n"
                    body += f"/std 최근n일 형태로 입력해 주세요.\n"
                    body += f"서버과부하 방지를 위해 조회는 최근 3일까지만 가능합니다.\n"
                    body += f"ex) /std 1  -> 최근 1일 간의 1분봉 종가 표준편차"
                    self.bot.send_thread(chat_id=user_id, text=body)
                    return

                if len(input_msg) != 1:
                    body = f"잘못된 입력입니다. /std 를 입력하여 사용법을 확인 해 주세요."
                    self.bot.send_thread(chat_id=user_id, text=body)
                    return
                
                try:
                    timedelta_day = int(input_msg[0])
                except:
                    body = f"잘못된 입력입니다. /std 를 입력하여 사용법을 확인 해 주세요."
                    self.bot.send_thread(chat_id=user_id, text=body)
                    return

                if timedelta_day < 1:
                    body = f"숫자는 양수만 입력이 가능합니다."
                    self.bot.send_thread(chat_id=user_id, text=body)
                    return

                if timedelta_day > 3:
                    body = f"서버 과부하 방지를 위해 최대 조회 일수는 3일까지만 가능합니다."
                    self.bot.send_thread(chat_id=user_id, text=body)
                    return

                datetime_now = datetime.datetime.now()
                datetime_start = datetime_now - datetime.timedelta(days=timedelta_day)
                body = f"{len(self.get_both_listed_okx_symbols())}개 코인에 대한 데이터를 프로세싱 중입니다.\n"
                body += f"잠시만 기다려 주세요.."
                self.bot.send_thread(chat_id=user_id, text=body)

                manager = Manager()
                return_dict = manager.dict()
                unit_period = 1 # use 1min candles
                kimp_std_df_proc = Process(target=self.data_processor.calculate_kimp_std, args=([x.replace('-USDT-SWAP', '') for x in self.get_both_listed_okx_symbols()], datetime_start, unit_period, return_dict), daemon=True)
                kimp_std_df_proc.start()
                kimp_std_df_proc.join()
                kimp_std_df = return_dict['res']

                body = f"최근 {timedelta_day}일 1분봉 김프 변동성(표준편차)\n"
                for tup in kimp_std_df.iterrows():
                    index = tup[0]
                    row = tup[1]
                    body += f"\n{row['symbol']}|{round(row['kimp_std']*100, 3)}%"
                self.bot.send_thread(chat_id=user_id, text=body)
            except Exception as e:
                self.telegram_bot_logger.error(f"std|{traceback.format_exc()}")
                body = f"서비스에 불편을 드려 죄송합니다. 일시적인 오류가 발생했습니다. 관리자에게 문의 해 주세요. (@charlie1155)\n"
                body += f"error: {e}"
                self.bot.send_thread(chat_id=user_id, text=body)
                return
        std_thread_th = Thread(target=std_thread, daemon=True)
        std_thread_th.start()
     
    def info(self, update, context):
        def info_thread():
            self.get_log('info', update, context)
            user_id = update.effective_chat.id
            try:
                user_series = self.snatcher.userinfo_df[self.snatcher.userinfo_df['user_id']==user_id].iloc[0,:]
                user_api_key_df = self.snatcher.user_api_key_df[self.snatcher.user_api_key_df['user_id']==user_id]

                # User service time
                user_datetime_end_seconds = max((user_series['datetime_end'] - datetime.datetime.now()).total_seconds(), 0)
                if user_datetime_end_seconds == 0:
                    user_datetime_end_str = '사용기간만료'
                else:
                    days = (user_datetime_end_seconds/60/60)//24
                    hours = (user_datetime_end_seconds/60/60)%24//1
                    minutes = (((user_datetime_end_seconds)/60/60)%24%1) * 60
                    user_datetime_end_str = f'{round(days)}일 {round(hours)}시간 {round(minutes)}분 남음'

                # # User diff
                # if user_series['kimp_diff_sign'] == None:
                #     user_kimp_diff_sign_str = ''
                # elif user_series['kimp_diff_sign'] == 0:
                #     user_kimp_diff_sign_str = '-'
                # else:
                #     user_kimp_diff_sign_str = '+'

                # User okx margin mode
                if user_series['okx_cross'] == 0:
                    okx_cross_str = "격리(Isolated)모드"
                elif user_series['okx_cross'] == 1:
                    okx_cross_str = "교차(Cross)모드"
                else:
                    okx_cross_str = None

                # User margin monitor setting
                user_margin_monitor = user_series['okx_margin_call']
                if user_margin_monitor == None:
                    mar_str = '청산 모니터링 기능 비활성'
                elif user_margin_monitor == 1:
                    mar_str = '청산 경고 메시지 발신'
                elif user_margin_monitor == 2:
                    mar_str = '청산 경고 메시지 발신 및 김프거래 자동정리'
                else:
                    mar_str = '에러'

                user_safe_reverse = user_series['safe_reverse']
                if user_safe_reverse == None or user_safe_reverse == 0:
                    safe_str = "역매매 기능 꺼짐"
                else:
                    safe_str = "역매매 기능 작동 중"

                user_kimp_diff = user_series['kimp_diff']
                if user_kimp_diff == None:
                    user_kimp_diff_str = "없음"
                else:
                    user_kimp_diff_str = f"{user_kimp_diff}%"

                # User api key check
                upbit_api_key_num = len(user_api_key_df[user_api_key_df['exchange']=='UPBIT'])
                if upbit_api_key_num == 0:
                    upbit_api_key_num_str = '없음'
                else:
                    upbit_api_key_num_str = f"{upbit_api_key_num}개"
                okx_api_key_num = len(user_api_key_df[user_api_key_df['exchange']=='OKX'])
                if okx_api_key_num == 0:
                    okx_api_key_num_str = '없음'
                else:
                    okx_api_key_num_str = f"{okx_api_key_num}개"

                body = f"최초등록시각: {user_series['datetime'].strftime('%Y년 %m월 %d일 %H시 %M분')}"
                body += f"\n서비스종료시각: {user_series['datetime_end'].strftime('%Y년 %m월 %d일 %H시 %M분')}"
                body += f'\n남은 이용기간: <b>{user_datetime_end_str}</b>'
                body += f'\n\n<b>저장된 기타설정값</b>'
                body += f"\n알람설정: {user_series['alarm_num']}회, {user_series['alarm_period']}초 간격"
                body += f"\nOKX 레버리지: {user_series['okx_leverage']}배"
                body += f"\nOKX 마진모드: {okx_cross_str}"
                body += f"\nOKX 청산 모니터링: {mar_str}"
                body += f"\n역매매 안전장치: {safe_str}"
                body += f"\n김프괴리 감지설정값: {user_kimp_diff_str}"
                body += f"\n등록된 업비트 API KEY: {upbit_api_key_num_str}"
                body += f"\n등록된 OKX API KEY: {okx_api_key_num_str}"
                body += f"\n\n등록된 관심코인: {user_series['interest_coin']}"
                self.bot.send_thread(user_id, body, parse_mode=telegram.ParseMode.HTML)
                
            except Exception as e:
                self.telegram_bot_logger.error(f"info|{traceback.format_exc()}")
                body = f"서비스에 불편을 드려 죄송합니다. 일시적인 오류가 발생했습니다. 관리자에게 문의 해 주세요. (@charlie1155)\n"
                body += f"error: {e}"
                self.bot.send_thread(chat_id=user_id, text=body)
                return
        info_thread_th = Thread(target=info_thread, daemon=True)
        info_thread_th.start()
    
    def coupon(self, update, context):
        def coupon_thread():
            self.get_log('coupon', update, context, 'executive')
            user_id = update.effective_chat.id
            # Payment check
            auth = self.authorize(user_id)
            if auth is False:
                return
            try:
                # Check whether the user is a validated executive
                db_client = InitDBClient(**self.remote_db_dict)
                db_client.curr.execute("""SELECT * FROM executives""")
                executives_df = pd.DataFrame(db_client.curr.fetchall())
                db_client.conn.close()
                if len(executives_df) == 0:
                    body = f"운영진으로 등록되지 않은 유저입니다.\n"
                    body += f"관리자(@charlie1155)에게 문의하여 주시기 바랍니다."
                    self.bot.send_thread(user_id, body)
                    return
                else:
                    if user_id not in executives_df['user_id'].to_list():
                        body = f"운영진으로 등록되지 않은 유저입니다.\n"
                        body += f"관리자(@charlie1155)에게 문의하여 주시기 바랍니다."
                        self.bot.send_thread(user_id, body)
                        return
                if context.args == []:
                    body = f"영업용 추천인쿠폰을 생성하는 명령어 입니다.\n"
                    body += f"'/coupon 쿠폰메모' 형식으로 입력 해 주세요.\n"
                    body += f"생성된 쿠폰의 쿠폰코드를 사용자에게 전달하면, 사용자가 /refer 쿠폰코드 형식으로 등록하여 사용이 가능하며,\n"
                    body += f"사용 시, 무료이용기간 {self.free_service_period}일이 자동 부여됩니다.\n"
                    body += f"쿠폰메모는 어떠한 이용자가 쿠폰을 이용하였는지 발급자가 추후 식별할 수 있도록 하기 위한 목적이며,\n"
                    body += f"발급용도 혹은 쿠폰을 받을 사람의 이름을 입력하세요.\n"
                    body += f"동일한 쿠폰에 대하여 중복사용은 불가능하며,\n"
                    body += f"여러명 혹은 여러번 사용해야 할 경우, 쿠폰을 여러 개 발급 해 주세요.\n\n"
                    body += f"<b>현재 발급된 추천인쿠폰 목록</b>"

                    db_client = InitDBClient(**self.remote_db_dict)
                    db_client.curr.execute("""SELECT * FROM refer_coupon""")
                    refer_coupon_df = pd.DataFrame(db_client.curr.fetchall())
                    db_client.conn.close()
                    if len(refer_coupon_df) == 0:
                        body += "\n없음"
                    else:
                        for row_tup in refer_coupon_df.iterrows():
                            index = row_tup[0]
                            row = row_tup[1]
                            if row['used_flag'] == 0:
                                used_str = '미사용'
                            else:
                                used_str = '<b>사용됨</b>'
                            body += f"\n<b>{index+1}.</b> 쿠폰코드: <b>{row['coupon_uuid']}</b>({used_str})"
                            body += f"\n   쿠폰메모: {row['coupon_memo']}"
                    self.bot.send_thread_split_by_number(user_id, body)
                    return
                input_msg = ''.join(context.args).split(',')
                if len(input_msg) != 1:
                    body = f"잘못된 입력입니다.\n"
                    body += f"/coupon 명령어를 입력하여 사용방법을 확인 해 주세요."
                    self.bot.send_thread(chat_id=user_id, text=body)
                    return
                
                # Passed validation
                coupon_memo = input_msg[0]
                db_client = InitDBClient(**self.remote_db_dict)
                db_client.curr.execute("""SELECT user_name FROM executives WHERE user_id=%s""", user_id)
                user_name = db_client.curr.fetchall()[0]['user_name']
                val = [user_id, user_name, str(uuid.uuid4()), coupon_memo, self.free_service_period, 0]
                db_client.curr.execute("""INSERT INTO refer_coupon (user_id, user_name, coupon_uuid, coupon_memo, service_period, used_flag) VALUES(%s,%s,%s,%s,%s,%s)""", val)
                db_client.conn.commit()
                body = f"추천인쿠폰이 정상정으로 발급되었습니다.\n\n"
                body += f"<b>현재 발급된 추천인쿠폰 목록</b>"
                db_client.curr.execute("""SELECT * FROM refer_coupon""")
                refer_coupon_df = pd.DataFrame(db_client.curr.fetchall())
                db_client.conn.close()
                if len(refer_coupon_df) == 0:
                    body += "\n없음"
                else:
                    for row_tup in refer_coupon_df.iterrows():
                        index = row_tup[0]
                        row = row_tup[1]
                        if row['used_flag'] == 0:
                            used_str = '미사용'
                        else:
                            used_str = '<b>사용됨</b>'
                        body += f"\n<b>{index+1}.</b> 쿠폰코드: <b>{row['coupon_uuid']}</b>({used_str})"
                        body += f"\n   쿠폰메모: {row['coupon_memo']}"
                self.bot.send_thread_split_by_number(user_id, body)
            except Exception as e:
                self.telegram_bot_logger.error(f"coupon|{traceback.format_exc()}")
                body = f"서비스에 불편을 드려 죄송합니다. 일시적인 오류가 발생했습니다. 관리자에게 문의 해 주세요. (@charlie1155)\n"
                body += f"error: {e}"
                self.bot.send_thread(chat_id=user_id, text=body)
                return
        coupon_thread_th = Thread(target=coupon_thread, daemon=True)
        coupon_thread_th.start()

    def refer(self, update, context):
        def refer_thread():
            self.get_log('refer', update, context)
            user_id = update.effective_chat.id
            try:
                if context.args == []:
                    body = f"추천인쿠폰을 사용하는 명령어 입니다.\n"
                    body += f"'/refer 쿠폰코드' 형식으로 입력 해 주세요.\n"
                    body += f"ex) /refer d1f84c71-40bf-4d4f-b6d5-2350391115d9\n"
                    body += f"쿠폰은 중복사용이 불가능하며, 양도하실 수 없습니다.\n"
                    self.bot.send_thread(user_id, body)
                    return
                input_msg = ''.join(context.args).split(',')
                if len(input_msg) != 1:
                    body = f"잘못된 입력입니다.\n"
                    body += f"/refer 명령어를 입력하여 사용방법을 확인 해 주세요."
                    self.bot.send_thread(chat_id=user_id, text=body)
                    return
                
                coupon_uuid = input_msg[0]
                db_client = InitDBClient(**self.remote_db_dict)
                db_client.curr.execute("""SELECT * FROM refer_coupon WHERE coupon_uuid=%s""", coupon_uuid)
                coupon_df = pd.DataFrame(db_client.curr.fetchall())
                db_client.conn.close()
                if len(coupon_df) == 0:
                    body = f"유효하지 않은 쿠폰코드입니다.\n"
                    body += f"코드를 다시 한 번 확인 해 주세요."
                    self.bot.send_thread(user_id, body)
                    return
                coupon_used_flag = int(coupon_df['used_flag'].values[0])
                if coupon_used_flag:
                    body = f"이미 사용된 쿠폰입니다."
                    self.bot.send_thread(user_id, body)
                    return
                # Passed validation
                coupon_service_period = int(coupon_df['service_period'].values[0])
                issuer_user_id = int(coupon_df['user_id'].values[0])
                val = [1, self.node, user_id]
                db_client = InitDBClient(**self.remote_db_dict)
                db_client.curr.execute("""UPDATE refer_coupon SET used_flag=%s, used_node=%s, used_by_user_id=%s""", val)
                db_client.conn.commit()
                db_client.conn.close()

                # Extend service period for one user
                db_client = InitDBClient(**self.local_db_dict)
                db_client.curr.execute("""SELECT * FROM user_info;""")
                fetched = db_client.curr.fetchall()
                user_info_df = pd.DataFrame(fetched)
                datetime_end = user_info_df[user_info_df['user_id'] == user_id]['datetime_end'].iloc[0]

                if datetime_end < datetime.datetime.now():
                    new_datetime_end = datetime.datetime.now() + datetime.timedelta(days=coupon_service_period)
                else:
                    new_datetime_end = datetime_end + datetime.timedelta(days=coupon_service_period)
                try:
                    db_client.curr.execute("""UPDATE user_info SET datetime_end=%s WHERE user_id=%s""", (new_datetime_end.to_pydatetime(), user_id))
                except:
                    db_client.curr.execute("""UPDATE user_info SET datetime_end=%s WHERE user_id=%s""", (new_datetime_end, user_id))
                db_client.conn.commit()
                db_client.conn.close()

                body = f"추천인쿠폰이 정상적으로 적용되어 이용기간 {coupon_service_period}일이 연장되었습니다.\n"
                body += f"연장된 이용기간은 /info 명령어를 이용하여 확인가능합니다."
                self.bot.send_thread(user_id, body)

                body = f"유저ID: {user_id} 님이 쿠폰을 사용하여 쿠폰이용기간 {coupon_service_period}일이 부여되었습니다."
                self.bot.send_thread(issuer_user_id, body)
            except Exception as e:
                self.telegram_bot_logger.error(f"refer|{traceback.format_exc()}")
                body = f"서비스에 불편을 드려 죄송합니다. 일시적인 오류가 발생했습니다. 관리자에게 문의 해 주세요. (@charlie1155)\n"
                body += f"error: {e}"
                self.bot.send_thread(chat_id=user_id, text=body)
                return
        refer_thread_th = Thread(target=refer_thread, daemon=True)
        refer_thread_th.start()

############# Functions for management ###########################################################################
    def ext(self, update, context):
        def ext_thread():
            self.get_log('ext', update, context, 'admin')
            if update.effective_chat.id != self.admin_id:
                return
            
            input_msg_list = ''.join(context.args).split(',')
            if len(input_msg_list) != 2:
                self.bot.send_thread(chat_id=self.admin_id, text=f'Input Error!')
                return
            
            try:
                target_user_id = int(input_msg_list[0])
                period_to_extend = int(input_msg_list[1])

                # Extend service period for one user
                user_id = target_user_id
                days = period_to_extend

                db_client = InitDBClient(**self.local_db_dict)
                db_client.curr.execute("""SELECT * FROM user_info;""")
                fetched = db_client.curr.fetchall()
                db_client.conn.close()
                user_info_df = pd.DataFrame(fetched)
                datetime_end = user_info_df[user_info_df['user_id'] == user_id]['datetime_end'].iloc[0]

                if datetime_end < datetime.datetime.now():
                    new_datetime_end = datetime.datetime.now() + datetime.timedelta(days=days)
                else:
                    new_datetime_end = datetime_end + datetime.timedelta(days=days)
                db_client = InitDBClient(**self.local_db_dict)
                try:
                    db_client.curr.execute("""UPDATE user_info SET datetime_end=%s WHERE user_id=%s""", (new_datetime_end.to_pydatetime(), user_id))
                except:
                    db_client.curr.execute("""UPDATE user_info SET datetime_end=%s WHERE user_id=%s""", (new_datetime_end, user_id))
                db_client.conn.commit()
                db_client.conn.close()

                body = f'user_id: {user_id}'
                body += f'\nuser_datetime_end before ext: {datetime_end}'
                body += f'\nextended days: {days}'
                body += f'\nupdated datetime end: {new_datetime_end}'
                self.bot.send_thread(chat_id=self.admin_id, text=body)
                body2 = f"이용기간이 {days}일 연장되었습니다.\n이용해 주셔서 감사드립니다.\n"
                body2 += f"서비스 이용기간 만료일: {new_datetime_end}"
                self.bot.send_thread(chat_id=user_id, text=body2)
                return

            except Exception as e:
                self.telegram_bot_logger.error(f"ext|{traceback.format_exc()}")
                self.bot.send_thread(chat_id=self.admin_id, text=f'Error occured while processing ext func, {e}')
                return
        ext_thread_th = Thread(target=ext_thread, daemon=True)
        ext_thread_th.start()

    def extall(self, update, context):
        def extall_thread():
            self.get_log('extall', update, context, 'admin')
            user_id = update.effective_chat.id
            if user_id != self.admin_id:
                return
            try:
                input_msg = ''.join(context.args).split(',')
                if len(input_msg) != 1:
                    body = f"Input Error!"
                    self.bot.send_thread(chat_id=user_id, text=body)
                    return
                days_to_extend = int(input_msg[0])

                # Load User info
                db_client = InitDBClient(**self.local_db_dict)
                db_client.curr.execute("""SELECT * FROM user_info;""")
                fetched = db_client.curr.fetchall()
                db_client.conn.close()
                user_info_df = pd.DataFrame(fetched)

                before_admin_datetime_end = user_info_df[user_info_df['user_id']==user_id]['datetime_end'].values[0]

                # UPDATE extended period
                db_client = InitDBClient(**self.local_db_dict)
                for row_tup in user_info_df.iterrows():
                    row = row_tup[1]
                    each_user_id = row['user_id']
                    datetime_end = row['datetime_end']

                    if datetime_end < (datetime.datetime.now() - datetime.timedelta(days=days_to_extend)):
                        continue

                    new_datetime_end = datetime_end + datetime.timedelta(days=days_to_extend) # days to extend
                    db_client.curr.execute("""UPDATE user_info SET datetime_end=%s WHERE user_id=%s""", (new_datetime_end.to_pydatetime(), each_user_id))
                db_client.conn.commit()
                db_client.conn.close()

                # Load User info to check
                db_client = InitDBClient(**self.local_db_dict)
                db_client.curr.execute("""SELECT datetime_end, user_id, user_name FROM user_info WHERE user_id=%s""", user_id)
                fetched = db_client.curr.fetchall()
                db_client.conn.close()

                after_admin_datetime_end = fetched[0]['datetime_end']

                body = f"before_admin_datetime_end: {before_admin_datetime_end}\n"
                body += f"after_admin_datetime_end: {after_admin_datetime_end}"
                self.bot.send_thread(chat_id=user_id, text=body)
                return
            except Exception as e:
                self.telegram_bot_logger.error(f"extall|{traceback.format_exc()}")
                self.bot.send_thread(chat_id=self.admin_id, text=f'Error occured while processing extall func, {e}')
                return
        extall_thread_th = Thread(target=extall_thread, daemon=True)
        extall_thread_th.start()
    
    def rec(self, update, context):
        self.get_log('rec', update, context, 'admin')
        user_id = update.effective_chat.id
        self.bot.send_thread(chat_id=self.admin_id, text=str(user_id))
        self.bot.send_thread(chat_id=user_id, text=f'식별 ID가 관리자에게 전송되었습니다. 잠시만 기다려 주세요.')
        return
    
    def msgall(self, update, context):
        def admin_message_thread():
            self.get_log('msgall', update, context, 'admin')
            user_id = update.effective_chat.id
            if user_id == self.admin_id:
                db_client = InitDBClient(**self.local_db_dict)
                db_client.curr.execute("""SELECT user_id FROM user_info""")
                db_client.conn.close()
                output = db_client.curr.fetchall()
                df = pd.DataFrame(output)
                input_msg = context.args

                def send(context, df, input_msg):
                    for user in df['user_id']:
                        try:
                            self.bot.send_thread(chat_id=int(user), text=' '.join(input_msg))
                        except Exception as e:
                            pass
                            # body = f"userid:{int(user)} blocked the bot, {e}"
                            # context.self.bot.send_thread(chat_id=admin_id, text=body)
                send_th = Thread(target=send, args=(context, df, input_msg), daemon=True)
                send_th.start()
        admin_message_thread_th = Thread(target=admin_message_thread, daemon=True)
        admin_message_thread_th.start()
    
    def msgto(self, update, context):
        def send_thread():
            self.get_log('msgto', update, context, 'admin')
            user_id = update.effective_chat.id
            if user_id == self.admin_id:
                try:
                    if context.args == []:
                        body = f"/msgto user_id message 형식으로 입력하세요."
                        self.bot.send_thread(chat_id=self.admin_id, text=body)
                        return
                    input_msg = context.args
                    if len(input_msg) < 2:
                        body = f"잘못된 입력입니다.\n"
                        body += f"/send user_id message 형식으로 입력하세요."
                        self.bot.send_thread(chat_id=self.admin_id, text=body)
                        return
                    db_client = InitDBClient(**self.local_db_dict)
                    db_client.curr.execute("""SELECT user_id FROM user_info""")
                    db_client.conn.close()
                    output = db_client.curr.fetchall()
                    user_id_list = pd.DataFrame(output)['user_id'].tolist()
                    input_user_id = int(input_msg[0].replace(',',''))
                    if input_user_id not in user_id_list:
                        body = f"user_id: {input_user_id}는 Database에 등록된 유저가 아닙니다."
                        self.bot.send_thread(chat_id=self.admin_id, text=body)
                        return
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
    
    def addexec(self, update, context):
        def addexec_thread():
            self.get_log('addexec', update, context, 'admin')
            user_id = update.effective_chat.id
            if user_id == self.admin_id:
                try:
                    if context.args == []:
                        body = f"/addexec user_id, 이름 형식으로 입력하세요.\n\n"
                        body += f"<b>현재 등록된 운영진 목록</b>"

                        db_client = InitDBClient(**self.remote_db_dict)
                        db_client.curr.execute("""SELECT * FROM executives""")
                        executives_df = pd.DataFrame(db_client.curr.fetchall())
                        db_client.conn.close()
                        if len(executives_df) == 0:
                            body += "\n없음"
                        else:
                            for row_tup in executives_df.iterrows():
                                index = row_tup[0]
                                row = row_tup[1]
                                body += f"\n{index+1}. {row['user_id']}: {row['user_name']}"
                        self.bot.send_thread(chat_id=self.admin_id, text=body, parse_mode='html')
                        return
                    input_msg = ''.join(context.args).split(',')
                    if len(input_msg) != 2:
                        body = f"잘못된 입력입니다.\n"
                        body += f"/addexec user_id, 이름 형식으로 입력하세요."
                        self.bot.send_thread(chat_id=self.admin_id, text=body)
                        return
                    
                    # Passed validation
                    add_user_id = input_msg[0]
                    user_name = input_msg[1]
                    db_client = InitDBClient(**self.remote_db_dict)
                    val = [add_user_id, user_name]
                    db_client.curr.execute("""INSERT INTO executives (user_id, user_name) VALUES(%s, %s)""", val)
                    db_client.conn.commit()

                    body = f"user_id: {add_user_id} ({user_name}) 이(가) 운영진으로 등록되었습니다.\n\n"
                    body += f"<b>현재 등록된 운영진 목록</b>"
                    db_client.curr.execute("""SELECT * FROM executives""")
                    executives_df = pd.DataFrame(db_client.curr.fetchall())
                    db_client.conn.close()
                    if len(executives_df) == 0:
                        body += "\n없음"
                    else:
                        for row_tup in executives_df.iterrows():
                            index = row_tup[0]
                            row = row_tup[1]
                            body += f"\n{index+1}. {row['user_id']}: {row['user_name']}"
                    self.bot.send_thread(chat_id=user_id, text=body, parse_mode='html')
                    return
                except Exception as e:
                    self.telegram_bot_logger.error(f"addexec|{traceback.format_exc()}")
                    body = f"서비스에 불편을 드려 죄송합니다. 일시적인 오류가 발생했습니다. 관리자에게 문의 해 주세요. (@charlie1155)\n"
                    body += f"error: {e}"
                    self.bot.send_thread(chat_id=user_id, text=body)
                    return
        addexec_thread_th = Thread(target=addexec_thread, daemon=True)
        addexec_thread_th.start()

    def rmexec(self, update, context):
        def rmexec_thread():
            self.get_log('rmexec', update, context, 'admin')
            user_id = update.effective_chat.id
            if user_id == self.admin_id:
                try:
                    if context.args == []:
                        body = f"삭제할 운영진의 user_id 의 /rmexec user_id 형식으로 입력하세요.\n\n"
                        body += f"<b>현재 등록된 운영진 목록</b>"

                        db_client = InitDBClient(**self.remote_db_dict)
                        db_client.curr.execute("""SELECT * FROM executives""")
                        executives_df = pd.DataFrame(db_client.curr.fetchall())
                        db_client.conn.close()
                        if len(executives_df) == 0:
                            body += "\n없음"
                        else:
                            for row_tup in executives_df.iterrows():
                                index = row_tup[0]
                                row = row_tup[1]
                                body += f"\n{index+1}. {row['user_id']}: {row['user_name']}"
                        self.bot.send_thread(chat_id=self.admin_id, text=body, parse_mode='html')
                        return
                    input_msg = ''.join(context.args).split(',')
                    if len(input_msg) != 1:
                        body = f"잘못된 입력입니다.\n"
                        body += f"/rmexec user_id 형식으로 입력하세요."
                        self.bot.send_thread(chat_id=self.admin_id, text=body)
                        return
                    
                    # Passed validation
                    rm_user_id = input_msg[0]
                    db_client = InitDBClient(**self.remote_db_dict)
                    db_client.curr.execute("""DELETE FROM executives WHERE user_id=%s""", rm_user_id)
                    db_client.conn.commit()

                    body = f"user_id: {rm_user_id} 이(가) 운영진 목록에서 삭제되었습니다.\n\n"
                    body += f"<b>현재 등록된 운영진 목록</b>"
                    db_client.curr.execute("""SELECT * FROM executives""")
                    executives_df = pd.DataFrame(db_client.curr.fetchall())
                    db_client.conn.close()
                    if len(executives_df) == 0:
                        body += "\n없음"
                    else:
                        for row_tup in executives_df.iterrows():
                            index = row_tup[0]
                            row = row_tup[1]
                            body += f"\n{index+1}. {row['user_id']}: {row['user_name']}"
                    self.bot.send_thread(chat_id=user_id, text=body, parse_mode='html')
                    return
                except Exception as e:
                    self.telegram_bot_logger.error(f"rmexec|{traceback.format_exc()}")
                    body = f"서비스에 불편을 드려 죄송합니다. 일시적인 오류가 발생했습니다. 관리자에게 문의 해 주세요. (@charlie1155)\n"
                    body += f"error: {e}"
                    self.bot.send_thread(chat_id=user_id, text=body)
                    return
        rmexec_thread_th = Thread(target=rmexec_thread, daemon=True)
        rmexec_thread_th.start()

    def status(self, update, context):
        def status_thread():
            self.get_log('status', update, context, 'admin')
            user_id = update.effective_chat.id
            if user_id in [self.admin_id, 1007931055, 1976936977, 1100166438]:  # 나, 영익이형, 준우형, 홍갑이형
                try:
                    websocket_integrity_flag, whole_status_str = self.websocket_proc_status_func()
                    dollar_update_integrity_flag, dollar_update_status_str = self.dollar_update_thread_status()
                    kline_fetcher_integrity_flag, kline_fetcher_status_str = self.kline_fetcher_proc_status()
                    body = whole_status_str + '\n'
                    body += f"\nDollar Update Thread Status"
                    body += f'\n{dollar_update_status_str}'
                    body += f"\n\nKline Fetcher Proc Status"
                    body += f"\n{kline_fetcher_status_str}"
                
                    self.bot.send_thread(chat_id=user_id, text=body)
                except Exception as e:
                    self.telegram_bot_logger.error(f"status|{traceback.format_exc()}")
                    body = f"서비스에 불편을 드려 죄송합니다. 일시적인 오류가 발생했습니다. 관리자에게 문의 해 주세요. (@charlie1155)\n"
                    body += f"error: {e}"
                    self.bot.send_thread(chat_id=user_id, text=body)
                    return
        status_thread_th = Thread(target=status_thread, daemon=True)
        status_thread_th.start()


    # For Telegram binding with Web user (Web Version integration)
    def email(self, update, context):
        def email_thread():
            self.get_log('email', update, context)
            user_id = update.effective_chat.id
            try:
                input_msg = ''.join(context.args).split(',')
                if context.args == []:
                    body = f"김프봇 웹 아이디와 텔레그램 아이디를 바인딩하는 명령어 입니다.\n"
                    body += f"'/email 이메일주소' 형식으로 입력해 주세요.\n"
                    body += f"이메일은 김프봇 웹 회원가입에 사용한 주소와 동일해야 합니다.\n"
                    body += f"ex) /email people9@naver.com"
                    self.bot.send_thread(chat_id=user_id, text=body)
                    return

                if len(input_msg) != 1:
                    body = f"잘못된 입력입니다. /beta 를 입력하여 사용법을 확인 해 주세요."
                    self.bot.send_thread(chat_id=user_id, text=body)
                    return

                input_email = input_msg[0]
                encoded_email = base64.b64encode(str(input_email).encode('utf-8')).decode('utf-8')
                # base64.b64decode(encoded_email).decode('utf-8') # decode
                encoded_user_id = base64.b64encode(str(user_id).encode('utf-8')).decode('utf-8') # 5490236140
                # base64.b64decode(encoded_user_id).decode('utf-8') # decode
                # domain = '222.106.173.213:22180' # Needed to be changed to Frontend server's domain
                # domain = 'localhost:8000' 
                domain = '218.153.174.26'
                auth_url = f'http://{domain}/telegram_activate/{encoded_email}/{encoded_user_id}'
                mail_title = "[김프봇 인증메일] 링크를 클릭하여 텔레그램계정을 연동하세요."
                mail_content = f"하단의 링크를 클릭하면 텔레그램 계정과 웹계정의 연동이 진행됩니다.\n"
                mail_content += f"{auth_url}"
                self.send_email(mail_title, mail_content, input_email)
                body = f"입력하신 이메일로 인증 메일이 전송되었습니다.\n"
                body += f"인증 메일의 링크를 클릭하여 텔레그램 계정과 웹계정의 연동을 진행해 주세요."
                self.bot.send_thread(chat_id=user_id, text=body)
                return
            except Exception as e:
                body = f"서비스에 불편을 드려 죄송합니다. 일시적인 오류가 발생했습니다. 관리자에게 문의 해 주세요. (@charlie1155)\n"
                body += f"error: {e}"
                self.bot.send_thread(chat_id=user_id, text=body)
                return
        email_thread_th = Thread(target=email_thread, daemon=True)
        email_thread_th.start()
    
    # System handling functions
    ######################################################################################
    def stop(self, update, context):
        self.get_log('stop', update, context)
        user_id = update.effective_chat.id
        if user_id != self.admin_id:
            return
        try:
            pm2_name = 'kp_trade_v2'
            self.bot.send_thread(chat_id=user_id, text=f"Stopping kimp bot... sending pm2 stop {pm2_name}")
            result = os.system(f"pm2 stop {pm2_name}")
            self.bot.send_thread(chat_id=user_id, text=result)
        except Exception as e:
            body = f"서비스에 불편을 드려 죄송합니다. 일시적인 오류가 발생했습니다. 관리자에게 문의 해 주세요. (@charlie1155)\n"
            body += f"error: {e}"
            self.bot.send_thread(chat_id=user_id, text=body)
            return
        
    def restart(self, update, context):
        self.get_log('restart', update, context)
        user_id = update.effective_chat.id
        if user_id not in [self.admin_id, 1007931055, 1976936977, 1100166438]: # 나, 영익이형, 준우형, 홍갑이형
            return
        try:
            systemd_name = 'kp_trade_v2'
            self.bot.send_message(chat_id=user_id, text=f"Restarting kimp bot... for {systemd_name}")
            restart_dir = os.getcwd() + '/restart.sh'
            os.system(restart_dir)
            self.bot.send_thread(chat_id=self.admin_id, text='After restart_proc executed.')
        except Exception as e:
            body = f"서비스에 불편을 드려 죄송합니다. 일시적인 오류가 발생했습니다. 관리자에게 문의 해 주세요. (@charlie1155)\n"
            body += f"error: {e}"
            self.bot.send_thread(chat_id=user_id, text=body)
            return
        
    def redollar(self, update, context):
        self.get_log('redollar', update, context)
        user_id = update.effective_chat.id
        if user_id not in [self.admin_id, 1007931055, 1976936977, 1100166438]: # 나, 영익이형, 준우형, 홍갑이형
            return
        try:
            systemd_name = 'kp_trade_v2'
            self.bot.send_message(chat_id=user_id, text=f"Reinitiating dollar_update_thread... for {systemd_name}")
            reinitiating_dollar_thread_res = self.reinitiate_dollar_update_thread()
            self.bot.send_thread(chat_id=self.admin_id, text=reinitiating_dollar_thread_res)
        except Exception as e:
            body = f"서비스에 불편을 드려 죄송합니다. 일시적인 오류가 발생했습니다. 관리자에게 문의 해 주세요. (@charlie1155)\n"
            body += f"error: {e}"
            self.bot.send_thread(chat_id=user_id, text=body)
            return

    ######################################################################################

    def process_message(self, update, context):
        def process_message_thread():
            user_input = update.message.text
            self.get_log('process_message', update, context=None, input_text=user_input)
            user_id = update.effective_chat.id
            if user_id not in [self.admin_id, 1007931055, 1976936977, 1100166438]: # 나, 영익이형, 준우형, 홍갑이형
                return

            user_input = update.message.text
            self.bot.send_thread(chat_id=user_id, text="인공지능 챗봇이 답변을 작성 중 입니다.\n답변까지는 최대 1분이 소요될 수 있습니다. 잠시만 기다려 주세요.")
            response_dict = {"finished": False}
            chatbot_reply_thread = Thread(target=self.chatbot.get_response, args=(user_input, response_dict), daemon=True)
            chatbot_reply_thread.start()
            while response_dict['finished'] is False:
                self.bot.send_chat_action(chat_id=user_id, action=telegram.ChatAction.TYPING)
                time.sleep(0.1)
            # reply_from_chatbot = self.chatbot.get_response(user_input)
            self.bot.send_thread(chat_id=user_id, text=response_dict['answer'])
        process_message_th = Thread(target=process_message_thread, daemon=True)
        process_message_th.start()


    # handling normal messages from user ######################################################################################
    # unknown command handler/ It must be located at the end of functions
    def unknown(self, update, context):
        text = f"없는 명령어 입니다. /help 를 입력하여 명령어를 확인해 주세요."
        self.bot.send_thread(chat_id=update.effective_chat.id, text=text)
    