import base64
import hashlib
import hmac
import json
import time
import urllib.parse
import os.path
import requests
import yaml

from pathlib import Path


def push_message(msg, is_at_all=False):
    cur_dir = Path(__file__).parent.parent.absolute()
    with open(os.path.join(cur_dir, 'config.yaml')) as file:
        config = yaml.safe_load(file)
        secret = config['DING_SECRET']
        token = config['DING_TOKEN']

    timestamp = str(round(time.time() * 1000))
    secret_enc = secret.encode("utf-8")
    string_to_sign = "{}\n{}".format(timestamp, secret)
    string_to_sign_enc = string_to_sign.encode("utf-8")
    hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
    sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
    send_data = {"at": {"isAtAll": is_at_all}, "msgtype": "text", "text": {"content": msg}}
    requests.post(
        url="https://oapi.dingtalk.com/robot/send?access_token={0}&timestamp={1}&sign={2}".format(
            token, timestamp, sign
        ),
        headers={"Content-Type": "application/json", "Charset": "UTF-8"},
        data=json.dumps(send_data),
    )
