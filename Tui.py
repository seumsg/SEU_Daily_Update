import requests


def server_post(Subject, Message, Sckey):
    url = 'https://sctapi.ftqq.com/' + Sckey + '.send'
    d = {'title': Subject, 'desp': Message}
    r = requests.post(url, data=d)

def bark_post(Subject, Message, Sckey):
    url = 'http://www.pushplus.plus/send?token='+Sckey+'&title='+Subject+'&content='+Message
    r = requests.get(url)

def kutui_post(Subject, Message, Kutui_key):
    url = 'https://push.xuthus.cc/send/' + Kutui_key + '?c=' + Subject + '\n\n' + Message
    r = requests.post(url)

def xuyuantu_bot_markdown(Subject, Message, Botkey):
    url = 'https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=' + Botkey
    markdown = {'msgtype': 'markdown', 'markdown': Message}
    r = requests.post(url, json=markdown)
