import requests
import datetime
import os, json, sys

# upper_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# sys.path.append(upper_dir)

# # Read custom setting json file
# file_name = 'kimp_bot_config.json'
# json_full_dir = os.path.join(upper_dir, file_name)
# with open(json_full_dir) as f:
#     json_settings = json.loads(f.read())
# admin_id = json_settings['telegram_admin_id']['charlie1155']

class RegisterMonitorMsg:
    def __init__(self, bot_token, api_url, admin_id):
        self.bot_token = bot_token
        self.api_url = api_url
        self.admin_id = admin_id

    # Registering monitor message through the Django backend server
    def register(self, target_telegram_id, origin, input_type, title, content=None, code=None, sent_switch=0, send_counts=1, remark=None):
        if type(sent_switch) != int:
            raise Exception("sent_switch is not int type.")
        if type(send_counts) != int:
            raise Exception("send_counts is not int type.")

        headers = {'Content-Type': 'application/json; charset=utf-8'}

        if type(target_telegram_id) != list:
            target_telegram_id_list = [target_telegram_id]
        else:
            target_telegram_id_list = target_telegram_id

        for each_target_telegram_id in target_telegram_id_list:
            data = {
                "bot_token": self.bot_token,
                "datetime": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "target_telegram_id": each_target_telegram_id,
                'origin': origin,
                "type": input_type,
                "title": title,
                "content": content,
                "code": code,
                "sent_switch": sent_switch,
                "send_counts": send_counts,
                "remark": remark
            }

            response = requests.post(self.api_url, data=json.dumps(data), headers=headers)
            if response.status_code != 201:
                print(f"response.json: {response.json()}")
                # raise Exception(f"data: {data}, response code: {response.status_code}, response: {response.json()}")
                admin_data = {
                    "bot_token": self.bot_token,
                    "datetime": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "target_telegram_id": self.admin_id,
                    "origin": "register_msg.register",
                    "type": "error",
                    "title": "Register Msg Error (kp_monitor_bot)",
                    "content": f"data: {data}, response code: {response.status_code}, response: {response.json()}",
                    "code": None,
                    "sent_switch": 0,
                    "send_counts": 1,
                    "remark": None
                }
                new_response = requests.post(self.api_url, data=json.dumps(data), headers=headers)
                print(f"new_response: {new_response.json()}")