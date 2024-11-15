import time
from acw_api import AcwApi
import pandas as pd
import os
import traceback
from loggers.logger import TradeCoreLogger

class CommandHandler:
    def __init__(self, acw_url, node, prod, admin_telegram_id, core, logging_dir):
        self.logger = TradeCoreLogger("command_handler", logging_dir).logger
        self.acw_api = AcwApi(acw_url, node, prod)
        self.node = node
        self.admin_telegram_id = admin_telegram_id
        self.core = core
        self.pm2_name = 'info_core'
        
    def fetch_command_loop(self):
        self.logger.info('Starting fetch_command_loop...')
        while True:
            time.sleep(1)
            try:
                self.fetch_command()
                time.sleep(1)
            except Exception as e:
                title = f'Error in fetch_command_loop'
                content = f'Error in fetch_command_loop: {e}'
                full_content = title + '\n' + content
                self.logger.error(full_content + '\n' + traceback.format_exc())
                # self.acw_api.create_message(self.admin_telegram_id, title, self.node, 'ERROR', full_content)
                time.sleep(1)
        
    def fetch_command(self):
        command_message_df = self.acw_api.get_message(type='COMMAND') # Need to be changed to 'command' when the API is ready
        if len(command_message_df) == 0:
            return
        command_message_df = command_message_df[(command_message_df['telegram_chat_id']==0)&(command_message_df['read']==False)&(command_message_df['title']==self.node)]
        if len(command_message_df) == 0:
            return
        for row_tup in command_message_df.iterrows():
            row = row_tup[1]
            id = row['id']
            # Change read to True via acw api
            self.acw_api.update_read_message(id)
            command = row['content']
            if command == 'status':
                self.status()
            elif command == 'kline_status':
                self.kline_status()
            elif command == 'start':
                self.start()
            elif command == 'stop':
                self.stop()
            elif command == 'restart':
                self.restart()
            else:
                title = f'Invalid command'
                content = f'Invalid command: {command}'
                content += '\nAvailable commands: status, start, stop, restart'
                full_content = title + '\n' + content
                self.acw_api.create_message(self.admin_telegram_id, title, full_content)
    
    def status(self):
        total_status, status_str = self.core.check_status(include_text=True)
        if total_status is False:
            total_status_str = '비정상'
        else:
            total_status_str = '정상'
        title = f"{self.node} CORE STATUS"
        content = total_status_str + '\n' + status_str
        full_content = title + '\n' + content
        self.acw_api.create_message(self.admin_telegram_id, title, full_content)
        
    def trade_status(self):
        total_status, status_str = self.core.check_trade_status(include_text=True)
        if total_status is False:
            total_status_str = '비정상'
        else:
            total_status_str = '정상'
        title = f"{self.node} TRADE STATUS"
        content = total_status_str + '\n' + status_str
        full_content = title + '\n' + content
        self.acw_api.create_message(self.admin_telegram_id, title, full_content)
        
    def start(self):
        return
    
    def stop(self):
        # register message
        title = f'Stopping {self.node}...'
        self.acw_api.create_message(self.admin_telegram_id, title, title)
        upper_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        restart_dir = upper_dir + '/stop.sh'
        os.system(restart_dir)
        return
    
    def restart(self):
        # register message
        title = f'Restarting {self.node}...'
        self.acw_api.create_message(self.admin_telegram_id, title, title)
        upper_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        restart_dir = upper_dir + '/restart.sh'
        os.system(restart_dir)
        return