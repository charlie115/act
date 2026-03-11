import datetime
from threading import Thread

import pandas as pd
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class AcwApi:
    def __init__(self, acw_url, node, prod, message_content_mode="inline"):
        self.verify = bool(prod)
        self.url = acw_url
        self.node = node
        self.message_content_mode = message_content_mode

        self.message_url = "messagecore/messages/"
        self.node_url = "tradecore/nodes/"
        self.referral_commission_url = "referral/referral-commission/"
        self.deposit_balance = "users/deposit-balance/"
        self.deposit_history = "users/deposit-history/"
        self.exchange_status = "exchange-status/server-status/"
        self.activated_market_codes = "infocore/market-codes/"

    def _raise_error(self, response):
        raise Exception(f"Error: {response.status_code}\n{response.text}")

    def _format_message_content(self, title, content, type_):
        if content is None:
            return None

        if self.message_content_mode == "monitor_newline":
            if type_.upper() in {"MONITOR", "DEBUG"}:
                return f"[{self.node}]\n{content}"
            return content

        return f"[{self.node}]{content}"

    def get_message(self, id=None, type=None):
        url = self.url + self.message_url
        params = {"type": type} if type is not None else None

        if id is not None:
            response = requests.get(
                url + str(id) + "/",
                verify=self.verify,
                params=params,
            )
            if response.status_code == 200:
                return pd.DataFrame([response.json()])
            self._raise_error(response)

        response = requests.get(url, verify=self.verify, params=params)
        if response.status_code == 200:
            return pd.DataFrame(response.json()["results"])
        self._raise_error(response)

    def create_message(
        self,
        telegram_chat_id,
        title,
        content=None,
        type="MONITOR",
        remark=None,
        code=None,
        sent=False,
        send_times=1,
        send_term=1,
    ):
        url = self.url + self.message_url
        payload = {
            "datetime": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S"),
            "telegram_chat_id": telegram_chat_id,
            "title": title,
            "origin": self.node,
            "type": type.upper(),
            "content": self._format_message_content(title, content, type),
            "remark": remark,
            "code": code,
            "sent": sent,
            "send_times": send_times,
            "send_term": send_term,
        }
        response = requests.post(url, json=payload, verify=self.verify)
        if response.status_code == 201:
            return response.json()
        self._raise_error(response)

    def update_read_message(self, id):
        url = self.url + self.message_url
        response = requests.patch(
            url + str(id) + "/",
            json={"read": True},
            verify=self.verify,
        )
        if response.status_code == 200:
            return response.json()
        self._raise_error(response)

    def create_message_thread(self, *args, **kwargs):
        thread = Thread(target=self.create_message, args=args, kwargs=kwargs, daemon=True)
        thread.start()

    def delete_message(self, id):
        url = self.url + self.message_url
        response = requests.delete(url + str(id) + "/", verify=self.verify)
        if response.status_code == 204:
            return True
        self._raise_error(response)

    def get_node(self, id=None):
        url = self.url + self.node_url
        if id is not None:
            response = requests.get(url + str(id) + "/", verify=self.verify)
            if response.status_code == 200:
                return pd.DataFrame([response.json()])
            self._raise_error(response)

        response = requests.get(url, verify=self.verify)
        if response.status_code == 200:
            return pd.DataFrame(response.json()["results"])
        self._raise_error(response)

    def get_referral_commission(
        self,
        user,
        trade_uuid,
        initial_profit,
        target_market_code=None,
        origin_market_code=None,
        apply_to_deposit=False,
    ):
        url = self.url + self.referral_commission_url
        params = {
            "user": user,
            "trade_uuid": trade_uuid,
            "initial_profit": initial_profit,
            "apply_to_deposit": apply_to_deposit,
        }
        if target_market_code is not None:
            params["target_market_code"] = target_market_code
        if origin_market_code is not None:
            params["origin_market_code"] = origin_market_code

        response = requests.get(url, params=params, verify=self.verify)
        if response.status_code == 200:
            return response.json()
        self._raise_error(response)

    def process_referral_fee_and_commission(
        self, user, trade_uuid, initial_profit, apply_to_deposit=False
    ):
        return self.get_referral_commission(
            user=user,
            trade_uuid=trade_uuid,
            initial_profit=initial_profit,
            apply_to_deposit=apply_to_deposit,
        )

    def get_deposit_history(self, user):
        url = self.url + self.deposit_history
        response = requests.get(
            url,
            params={"user": user},
            verify=self.verify,
        )
        if response.status_code == 200:
            return pd.DataFrame(response.json()["results"])
        self._raise_error(response)

    def create_deposit_history(
        self,
        user,
        balance,
        change,
        txid,
        type,
        pending,
        registered_datetime=datetime.datetime.utcnow(),
    ):
        url = self.url + self.deposit_history
        payload = {
            "user": user,
            "balance": balance,
            "change": change,
            "txid": txid,
            "type": type,
            "pending": pending,
            "registered_datetime": registered_datetime.strftime("%Y-%m-%dT%H:%M:%S"),
        }
        response = requests.post(url, json=payload, verify=self.verify)
        if response.status_code == 201:
            return response.json()
        self._raise_error(response)

    def get_deposit_balance(self, user=None):
        url = self.url + self.deposit_balance
        response = requests.get(
            url,
            params={"user": user},
            verify=self.verify,
        )
        if response.status_code == 200:
            return pd.DataFrame(response.json()["results"])
        self._raise_error(response)

    def get_exchange_status(self):
        url = self.url + self.exchange_status
        response = requests.get(url, verify=self.verify)
        if response.status_code == 200:
            return response.json()
        self._raise_error(response)

    def get_activated_market_codes(self):
        url = self.url + self.activated_market_codes
        response = requests.get(url, verify=self.verify)
        if response.status_code == 200:
            return response.json()
        self._raise_error(response)

