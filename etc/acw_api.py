import datetime
import pandas as pd
import requests
import os
import sys
import json
# uppend upper dir
upper_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(upper_dir + "/trade_core_config.json") as f:
    config = json.load(f)

node = config['node']
prod = config['node_settings'][node]['prod']

class AcwApi:
    def __init__(self, prod=prod):
        if prod is False:
            self.verify = False
            self.url = config['acw_setting']['dev_url']
        else:
            self.verify = True
            self.url = config['acw_setting']['prod_url']
        self.message_url = "messagecore/messages/"
        self.node_url = "tradecore/nodes/"

    def get_message(self, id=None):
        url = self.url + self.message_url
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
        
    def create_message(self, telegram_chat_id, title, origin, type, content=None, remark=None, code=None, sent=False, send_times=1, send_term=1):
        url = self.url + self.message_url
        new_message_dict = {
            "datetime": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S"),
            "telegram_chat_id": telegram_chat_id,
            "title": title,
            "origin": origin,
            "type": type,
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