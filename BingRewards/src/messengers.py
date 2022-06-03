import requests
from datetime import datetime
from abc import ABC, abstractmethod


class BaseMessenger(ABC):
    def __init__(self, messenger_type):
        self.messenger_type = messenger_type

    @abstractmethod
    def send_message(message):
        pass

    def handle_resp(self, resp):
        if (resp.status_code == 200
           ) or (self.messenger_type == 'discord' and resp.status_code == 204):
            print(f"{self.messenger_type.capitalize()} notification sent\n")
        else:
            print(
                f"Boo! {self.messenger_type.capitalize()} notification NOT sent, response code is: {resp} with response msg `{resp.text}`\n"
            )

    def send_reward_message(self, stats_str, run_hist_str, email):
        """
        This is the entry function that will be called in BinGRewards.py.
        In turn, this function will call send_message() which is a function customized for each Notification Service
        """
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message = f'\n Summary for {email} at : {current_time} \n\n' + \
        "\n".join(stats_str) + \
        f"\nRun Log: {[run_hist_str]}"

        self.send_message(message)


class TelegramMessenger(BaseMessenger):
    def __init__(self, api_token, userid):
        super().__init__('telegram')
        self.api_token = api_token
        self.userid = userid

    def send_message(self, message):
        reply_url = f'https://api.telegram.org/bot{self.api_token}/sendMessage?chat_id={self.userid}&text={message}'
        resp = requests.get(reply_url)
        self.handle_resp(resp)


class DiscordMessenger(BaseMessenger):
    def __init__(self, webhook_url):
        super().__init__('discord')
        self.webhook_url = webhook_url

    def send_message(self, message):
        content = {"username": "Bing Rewards Bot", "content": message}
        resp = requests.post(self.webhook_url, json=content)
        self.handle_resp(resp)
