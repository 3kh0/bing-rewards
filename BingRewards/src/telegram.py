import requests
from datetime import datetime


class TelegramMessenger():
    def __init__(self, api_token, userid):
        self.api_token = api_token
        self.userid = userid

    def send_message(self, message):
        reply_url = f'https://api.telegram.org/bot{self.api_token}/sendMessage?chat_id={self.userid}&text={message}'
        resp = requests.get(reply_url)
        if resp.status_code == 200:
            print("Telegram notification sent\n")
        else:
            print(f"Boo! Telegram notification NOT sent, response code is: {resp} with response msg {resp.text}\n")

    def send_reward_message(self, stats_str, run_hist_str, email):
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message = f'\n Summary for {email} at : {current_time} \n\n' + \
        "\n".join(stats_str) + \
        f"\nRun Log: {[run_hist_str]}"

        self.send_message(message)
