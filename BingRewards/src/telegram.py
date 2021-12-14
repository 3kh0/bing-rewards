import requests

class TelegramMessenger():
    def __init__(self, api_token, userid):
        self.api_token = api_token
        self.userid = userid

    def send_message(self, message):
        reply_url = f'https://api.telegram.org/bot{self.api_token}/sendMessage?chat_id={self.userid}&text={message}'
        resp = requests.get(reply_url)
        return resp
