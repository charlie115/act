import datetime
import pandas as pd
import requests
from threading import Thread
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning) # Should be removed in production

class AcwApi:
    def __init__(self, acw_url, node, prod):
        if prod is False:
            self.verify = False
        else:
            self.verify = True
        self.url = acw_url
        self.node = node
        self.message_url = "messagecore/messages/"
        self.node_url = "tradecore/nodes/"
        self.message_url = "messagecore/messages/"
        self.node_url = "tradecore/nodes/"
        self.referral_commission_url = "referral/referral-commission/"
        self.deposit_balance = "users/deposit-balance/"
        self.deposit_history = "users/deposit-history/"

    def get_message(self, id=None, type=None):
        url = self.url + self.message_url
        if type is not None:
                params = {
                    "type": type
                }
        else:
            params = None
        if id is not None:
            fetch_list = False
            response = requests.get(url + str(id) + "/", verify=self.verify, params=params)
        else:
            fetch_list = True
            response = requests.get(url, verify=self.verify, params=params)
        if response.status_code == 200:
            if fetch_list:
                return pd.DataFrame(response.json()["results"])
            else:
                return pd.DataFrame([response.json()])
        else:
            raise Exception("Error: " + str(response.status_code) + "\n" + response.text)
        
    def create_message(self, telegram_chat_id, title, content=None, type='MONITOR', remark=None, code=None, sent=False, send_times=1, send_term=1):
        url = self.url + self.message_url
        new_message_dict = {
            "datetime": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S"),
            "telegram_chat_id": telegram_chat_id,
            "title": title,
            "origin": self.node,
            "type": type.upper(),
            "content": content,
            "remark": remark,
            "code": code,
            "sent": sent,
            "send_times": send_times,
            "send_term": send_term
        }
        response = requests.post(url, json=new_message_dict, verify=self.verify)
        if response.status_code == 201:
            return response.json()
        else:
            raise Exception("Error: " + str(response.status_code) + "\n" + response.text)
        
    def update_read_message(self, id):
        url = self.url + self.message_url
        response = requests.patch(url + str(id) + "/", json={"read": True}, verify=self.verify)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception("Error: " + str(response.status_code) + "\n" + response.text)
        
    def create_message_thread(self, telegram_chat_id, title, content=None, type='MONITOR', remark=None, code=None, sent=False, send_times=1, send_term=1):
        t = Thread(target=self.create_message, args=(telegram_chat_id, title, content, type, remark, code, sent, send_times, send_term), daemon=True)
        t.start()

    def delete_message(self, id):
        url = self.url + self.message_url
        response = requests.delete(url + str(id) + "/", verify=self.verify)
        if response.status_code == 204:
            return True
        else:
            raise Exception("Error: " + str(response.status_code) + "\n" + response.text)
        
    def get_node(self, id=None):
        url = self.url + self.node_url
        if id is not None:
            fetch_list = False
            response = requests.get(url + str(id) + "/", verify=self.verify)
        else:
            fetch_list = True
            response = requests.get(url, verify=self.verify)
        if response.status_code == 200:
            if fetch_list:
                return pd.DataFrame(response.json()["results"])
            else:
                return pd.DataFrame([response.json()])
        else:
            raise Exception("Error: " + str(response.status_code) + "\n" + response.text)
        
    def get_referral_commission(self, user, trade_uuid, initial_profit, target_market_code, origin_market_code, apply_to_deposit=False):
        url = self.url + self.referral_commission_url
        response = requests.get(url, params={"user": user, "trade_uuid": trade_uuid, "initial_profit": initial_profit, "target_market_code": target_market_code, "origin_market_code": origin_market_code}, verify=self.verify)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception("Error: " + str(response.status_code) + "\n" + response.text)
        
    def get_deposit_history(self, user):
        url = self.url + self.deposit_history
        params = {
            "user": user
        }
        response = requests.get(url, params=params, verify=self.verify)
        if response.status_code == 200:
            return pd.DataFrame(response.json()["results"])
        else:
            raise Exception("Error: " + str(response.status_code) + "\n" + response.text)
        
    def create_deposit_history(self, user, balance, change, txid, type, pending, registered_datetime=datetime.datetime.utcnow()):
        url = self.url + self.deposit_history
        new_deposit_history_dict = {
            "user": user,
            "balance": balance,
            "change": change,
            "txid": txid,
            "type": type,
            "pending": pending,
            "registered_datetime": registered_datetime.strftime("%Y-%m-%dT%H:%M:%S")
        }
        response = requests.post(url, json=new_deposit_history_dict, verify=self.verify)
        if response.status_code == 201:
            return response.json()
        else:
            raise Exception("Error: " + str(response.status_code) + "\n" + response.text)
        
    def get_deposit_balance(self, user=None):
        url = self.url + self.deposit_balance
        params = {
            "user": user
        }
        response = requests.get(url, params=params, verify=self.verify)
        if response.status_code == 200:
            return pd.DataFrame(response.json()["results"])
        else:
            raise Exception("Error: " + str(response.status_code) + "\n" + response.text)