import datetime
import json
import os.path
import re
import time
import yaml
import requests

from pathlib import Path
from utils.message import push_message


def get_date():
    today = datetime.date.today()
    return "%4d%02d%02d" % (today.year, today.month, today.day)


def rsa_encrypt(password_str, e, m):
    password_bytes = bytes(password_str, 'ascii')
    password_int = int.from_bytes(password_bytes, 'big')
    result_int = pow(password_int, int(e, 16), int(m, 16))
    return hex(result_int)[2:].rjust(128, '0')


class HitCarder(object):
    def __init__(self, username, password):
        self.info = {}
        self.username = username
        self.password = password
        self.login_url = "https://zjuam.zju.edu.cn/cas/login?service=https%3A%2F%2Fhealthreport.zju.edu.cn%2Fa_zju%2Fapi%2Fsso%2Findex%3Fredirect%3Dhttps%253A%252F%252Fhealthreport.zju.edu.cn%252Fncov%252Fwap%252Fdefault%252Findex"
        self.base_url = "https://healthreport.zju.edu.cn/ncov/wap/default/index"
        self.save_url = "https://healthreport.zju.edu.cn/ncov/wap/default/save"
        self.sess = requests.Session()

    def login(self):
        res = self.sess.get(self.login_url)
        execution = re.search('name="execution" value="(.*?)"', res.text).group(1)
        res = self.sess.get(url='https://zjuam.zju.edu.cn/cas/v2/getPubKey').json()
        encrypt_password = rsa_encrypt(self.password, res['exponent'], res['modulus'])

        data = {
            'username': self.username,
            'password': encrypt_password,
            'execution': execution,
            '_eventId': 'submit'
        }
        res = self.sess.post(url=self.login_url, data=data)

        if '统一身份认证' in res.content.decode():
            raise RuntimeError('登录失败，请核实账号密码重新登录')
        return self.sess

    def post(self):
        res = self.sess.post(self.save_url, data=self.info)
        return json.loads(res.text)

    def get_info(self, html=None):
        if not html:
            res = self.sess.get(self.base_url)
            html = res.content.decode()

        old_infos = re.findall(r'oldInfo: ({[^\n]+})', html)
        if len(old_infos) != 0:
            old_info = json.loads(old_infos[0])
        else:
            raise RuntimeError("未发现缓存信息，请先至少手动成功打卡一次再运行脚本")

        new_id = json.loads(re.findall(r'def = ({[^\n]+})', html)[0])['id']
        name = re.findall(r'realname: "([^\"]+)",', html)[0]
        number = re.findall(r"number: '([^\']+)',", html)[0]

        self.info = old_info.copy()
        self.info['id'] = new_id
        self.info['name'] = name
        self.info['number'] = number
        self.info["date"] = get_date()
        self.info["created"] = round(time.time())

        self.info['jrdqtlqk[]'] = 0
        self.info['jrdqjcqk[]'] = 0
        self.info['sfsqhzjkk'] = 1  # 是否申领杭州健康码
        self.info['sqhzjkkys'] = 1  # 杭州健康吗颜色，1:绿色 2:红色 3:黄色
        self.info['sfqrxxss'] = 1  # 是否确认信息属实
        self.info['jcqzrq'] = ""
        self.info['gwszdd'] = ""
        self.info['szgjcs'] = ""


def main(username, password):
    hit_carder = HitCarder(username, password)
    try:
        hit_carder.login()
    except Exception as err:
        push_message('统一认证失败: ' + str(err), True)
        return

    try:
        hit_carder.get_info()
    except Exception as err:
        push_message('获取信息失败: ' + str(err), True)
        return

    pname = hit_carder.info['name'] + ' '
    try:
        res = hit_carder.post()
        if str(res['e']) == '0':
            push_message('{} 已为您打卡成功'.format(hit_carder.info['name']))
        else:
            push_message(hit_carder.info['name'] + ' ' + res['m'])
    except Exception as err:
        push_message('信息提交失败: ' + str(err), True)
        return


if __name__ == "__main__":
    cur_dir = Path(__file__).parent.absolute()
    with open(os.path.join(cur_dir, 'config.yaml')) as file:
        config = yaml.safe_load(file)
        accounts = config['ZJU_accout']

    for account in accounts:
        main(account['username'], account['password'])
