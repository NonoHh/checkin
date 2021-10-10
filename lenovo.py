from bs4 import BeautifulSoup
import requests
import os.path
import yaml

from pathlib import Path
from utils.message import push_message

class LenovoCheckIn:
    def __init__(self, username, password):
        self.username = username
        self.password = password

    def login(self):
        url = "https://reg.lenovo.com.cn/auth/v3/dologin"
        header = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.96 Safari/537.36",
            "Host": "reg.lenovo.com.cn",
            "Referer": "https://www.lenovo.com.cn/",
            'Cookie': 'LA_F_T_10000001=1614393605462; LA_C_Id=_ck21022710400514675618549440548; LA_M_W_10000001=_ck21022710400514675618549440548%7C10000001%7C%7C%7C; LA_C_C_Id=_sk202102271040090.05206000.3687; _ga=GA1.3.1245350653.1614393605; leid=1.VljlpE1LZ7I; LA_F_T_10000231=1614395016398; LA_R_T_10000231=1614395016398; LA_V_T_10000231=1614395016398; LA_M_W_10000231=_ck21022710400514675618549440548%7C10000231%7C%7C%7C; LA_R_C_10000001=1; LA_R_T_10000001=1614593722192; LA_V_T_10000001=1614593722192; _gid=GA1.3.1974081891.1614593723; _gat=1; ar=1'
        }
        data = {"account": self.username, "password": self.password,
                "ticket": "e40e7004-4c8a-4963-8564-31271a8337d8"}
        session = requests.Session()
        r = session.post(url, headers=header, data=data)
        if r.text.find("cerpreg-passport") == -1:  # 若未找到相关cookie则返回空值
            return None
        return session

    def signin(self, session):
        signin = session.get("https://i.lenovo.com.cn/signIn/add.jhtml?sts=e40e7004-4c8a-4963-8564-31271a8337d8",
                             headers={
                                 "user-agent": "Mozilla/5.0 (Linux; Android 11; Mi 10 Build/RKQ1.200826.002; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/86.0.4240.185 Mobile Safari/537.36/lenovoofficialapp/16112154380982287_10181446134/newversion/versioncode-124/"
                             })
        check = str(signin.text)
        if "true" in check:
            if "乐豆" in check:
                push_message("LENOVO签到成功")
            else:
                push_message("请不要重复LENOVO签到")
        else:
            push_message("LENOVO签到失败，请重试")

    def getContinuousDays(self, session):
        url = "https://club.lenovo.com.cn/signlist/"
        c = session.get(url, headers={
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.96 Safari/537.36",
        })
        soup = BeautifulSoup(c.text, "html.parser")
        day = soup.select(
            "body > div.signInMiddleWrapper > div > div.signInTimeInfo > div.signInTimeInfoMiddle > p.signInTimeMiddleBtn")
        day = day[0].get_text()
        return day

    def main(self):
        s = self.login()
        msg = f"帐号信息: {self.username}\n"
        if not s:
            msg += "Lenovo 登录失败，请检查账号密码"
        else:
            self.signin(s)
            day = self.getContinuousDays(s)
            msg += day
        push_message(msg)


if __name__ == "__main__":
    cur_dir = Path(__file__).parent.absolute()
    with open(os.path.join(cur_dir, 'config.yaml')) as file:
        config = yaml.safe_load(file)
        accounts = config['LENOVO_accout']

    for account in accounts:
        LenovoCheckIn(account['username'], account['password']).main()
