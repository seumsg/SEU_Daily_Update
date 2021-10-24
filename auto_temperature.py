# -*- coding: utf-8 -*
# Author：quzard
import datetime
import json
import re
from urllib import parse
from urllib.parse import parse_qs
import os
import execjs
import requests
import logging
import random
import time
import sys
from Tui import *
from time import sleep
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

# 登陆
def login(sess, uname, pwd):
    login_url = 'http://ehall.seu.edu.cn/ygfw/sys/xsqjappseuyangong/*default/index.do'
    get_login = sess.get(login_url)
    get_login.encoding = 'utf-8'
    lt = re.search('name="lt" value="(.*?)"', get_login.text).group(1)
    salt = re.search('id="pwdDefaultEncryptSalt" value="(.*?)"', get_login.text).group(1)
    execution = re.search('name="execution" value="(.*?)"', get_login.text).group(1)

    f = open("./encrypt.js", 'r', encoding='UTF-8')
    line = f.readline()
    js = ''
    while line:
        js = js + line
        line = f.readline()
    ctx = execjs.compile(js)
    password = ctx.call('_ep', pwd, salt)

    login_post_url = 'https://newids.seu.edu.cn/authserver/login?service=http%3A%2F%2Fehall.seu.edu.cn%2Fygfw%2Fsys%2Fxsqjappseuyangong%2F*default%2Findex.do'
    personal_info = {'username': uname,
                     'password': password,
                     'lt': lt,
                     'dllt': 'userNamePasswordLogin',
                     'execution': execution,
                     '_eventId': 'submit',
                     'rmShown': '1'}
    post_login = sess.post(login_post_url, personal_info)
    post_login.encoding = 'utf-8'
    if re.search("研究生出校登记审批", post_login.text):
        return True
    else:
        # logger.info(post_login.text)
        return False


# 设置header
def get_header(sess, cookie_url):
    get_cookie = sess.get(cookie_url)
    cookie = requests.utils.dict_from_cookiejar(sess.cookies)
    c = ""
    for key, value in cookie.items():
        c += key + "=" + value + "; "
    header = {'Referer': 'http://ehall.seu.edu.cn/ygfw/sys/xsqjappseuyangong/*default/index.do',
              'Cookie': c}
    return header

def get_wendu_header(sess, cookie_url):
    get_cookie = sess.get(cookie_url)
    weu = requests.utils.dict_from_cookiejar(get_cookie.cookies)['_WEU']
    cookie = requests.utils.dict_from_cookiejar(sess.cookies)
    header = {'Referer': 'http://ehall.seu.edu.cn/qljfwapp2/sys/lwReportEpidemicSeu/index.do',
              'Cookie': '_WEU=' + weu + '; MOD_AUTH_CAS=' + cookie['MOD_AUTH_CAS'] + ';'}
    return header


# 获取之前信息
def get_info(sess, header, username):
    personal_info_url = 'http://ehall.seu.edu.cn/ygfw/sys/xsqjappseuyangong/modules/wdqj/wdqjbg.do'
    get_personal_info = sess.post(personal_info_url, data={'XSBH': str(username), 'pageSize': '10', 'pageNumber': '1'},
                                  headers=header)
    return get_personal_info

def get_wendu_info(sess, header):
    personal_info_url = 'http://ehall.seu.edu.cn/qljfwapp2/sys/lwReportEpidemicSeu/modules/dailyReport/getMyDailyReportDatas.do'
    get_personal_info = sess.post(personal_info_url, data={'rysflb': 'BKS', 'pageSize': '10', 'pageNumber': '1'},
                                  headers=header)
    return get_personal_info

def get_info_2(sess, header, SQBH):
    url = "http://ehall.seu.edu.cn/ygfw/sys/xsqjappseuyangong/modules/wdqj/qjxqbd.do"
    header['Content-Type'] = 'application/x-www-form-urlencoded;charset=utf-8'
    FormData = {'SQBH': SQBH}
    data = parse.urlencode(FormData)

    get_personal_info = sess.post(url, data=data,
                                  headers=header)
    get_personal_info = json.loads(get_personal_info.text)['datas']['qjxqbd']['rows']
    get_personal_info = get_personal_info[0]
    return get_personal_info


# 获取未销假
def getAllNoRemoveLeave(sess, header, username):
    url = "http://ehall.seu.edu.cn/ygfw/sys/xsqjappseuyangong/modules/leaveApply/getAllNoRemoveLeave.do"
    header['Content-Type'] = 'application/x-www-form-urlencoded;charset=utf-8'
    FormData = {"requestParamStr": {'XSBH': str(username)}}
    data = parse.urlencode(FormData)

    get_personal_info = sess.post(url, data=data,
                                  headers=header)
    if "data" in get_personal_info.text:
        j = json.loads(get_personal_info.text)['data']
        return addXjApply(sess, header, j)
    return False


# 销假
def addXjApply(sess, header, datas):
    global msg_all
    url = "http://ehall.seu.edu.cn/ygfw/sys/xsqjappseuyangong/modules/leaveApply/addXjApply.do"
    header['Content-Type'] = 'application/x-www-form-urlencoded;charset=utf-8'
    for data in datas:
        now_time = datetime.datetime.now()
        if now_time.strftime("%Y-%m-%d") not in data['QJKSRQ'] and (now_time + datetime.timedelta(days=+1)).strftime(
                "%Y-%m-%d") not in data['QJKSRQ']:
            logger.info("销假: "+data["QJKSRQ"])
            msg_all += "销假: "+data["QJKSRQ"]+"\n"
            post_info = {
                "data": {"SQBH": "52b347e055e348c9abd2394694f3a613", "XSBH": 0, "SHZT": "20", "XJFS": "2",
                         "XJSJ": "", "XJRQ": "", "SQR": "", "SQRXM": "",
                         "THZT": "0"}}
            post_info["data"]["SQBH"] = data["SQBH"]
            post_info["data"]["XSBH"] = int(data["XSBH"])
            post_info["data"]["XJSJ"] = now_time.strftime("%Y-%m-%d %H:%M:%S")
            post_info["data"]["XJRQ"] = now_time.strftime("%Y-%m-%d")
            post_info["data"]["SQR"] = data["XSBH"]
            post_info["data"]["SQRXM"] = data["XM"]
            data = parse.urlencode(post_info)
            get_personal_info = sess.post(url, data=data,
                                          headers=header)
        else:
            if (now_time + datetime.timedelta(days=+1)).strftime("%Y-%m-%d") in data['QJKSRQ']:
                return True
    return False


# 获取未审批
def getAllApplyedLeave(sess, header, username):
    url = "http://ehall.seu.edu.cn/ygfw/sys/xsqjappseuyangong/modules/leaveApply/getAllApplyedLeave.do"
    header['Content-Type'] = 'application/x-www-form-urlencoded;charset=utf-8'
    FormData = {"requestParamStr": {'XSBH': str(username)}}
    data = parse.urlencode(FormData)

    get_personal_info = sess.post(url, data=data,
                                  headers=header)
    if "data" in get_personal_info.text:
        j = json.loads(get_personal_info.text)['data']
        return backleaveApply(sess, header, j)
    return False


# 撤回
def backleaveApply(sess, header, datas):
    global msg_all
    url = "http://ehall.seu.edu.cn/ygfw/sys/xsqjappseuyangong/modules/leaveApply/backleaveApply.do"
    header['Content-Type'] = 'application/x-www-form-urlencoded;charset=utf-8'
    for data in datas:
        now_time = datetime.datetime.now()
        # 未审批的今天和明天的不撤回
        if now_time.strftime("%Y-%m-%d") not in data['QJKSRQ'] and (now_time + datetime.timedelta(days=+1)).strftime(
                "%Y-%m-%d") not in data['QJKSRQ']:
            logger.info("撤回: "+data["QJKSRQ"])
            msg_all += "撤回: "+data["QJKSRQ"]+"\n"
            post_info = {"requestParamStr": {"SQBH": data["SQBH"]}}
            data = parse.urlencode(post_info)
            get_personal_info = sess.post(url, data=data,
                                          headers=header)
        else:
            return True
    return False


# 删除草稿
def delleaveApply(sess, header, datas):
    global msg_all
    url = "http://ehall.seu.edu.cn/ygfw/sys/xsqjappseuyangong/modules/leaveApply/delleaveApply.do"
    header['Content-Type'] = 'application/x-www-form-urlencoded;charset=utf-8'
    for data in datas:
        if data["SHZT_DISPALY_DISPLAY"] == "草稿":
            logger.info("删除草稿: "+data["QJKSRQ"])
            msg_all += "删除草稿: "+data["QJKSRQ"]+"\n"
            post_info = {"requestParamStr": {"SQBH": data["SQBH"]}}
            data = parse.urlencode(post_info)
            get_personal_info = sess.post(url, data=data,
                                          headers=header)


def askForLeave(sess, username):
    global msg_all
    cookie_url = 'http://ehall.seu.edu.cn/ygfw/sys/swpubapp/indexmenu/getAppConfig.do?appId=5869188708264821&appName=xsqjappseuyangong&v=06154290794922301'
    header = get_header(sess, cookie_url)

    # 获取未销假
    r = getAllNoRemoveLeave(sess, header, username)
    if r:
        logger.info("已有请假!  已经存在未销假的请假")
        msg_all += "已有请假!  已经存在未销假的请假"+"\n"
        return

    # 获取未审批
    r = getAllApplyedLeave(sess, header, username)
    if r:
        logger.info("已有请假!  已经存在未审批的请假")
        msg_all += "已有请假!  已经存在未审批的请假"+"\n"
        return
    # 删除草稿
    get_personal_info = get_info(sess, header, username)
    raw_personal_info = json.loads(get_personal_info.text)['datas']['wdqjbg']['rows']
    delleaveApply(sess, header, raw_personal_info)

    get_personal_info = get_info(sess, header, username)
    if get_personal_info.status_code == 200:
        logger.info('获取前一日信息成功!')
        msg_all += '获取前一日信息成功!'+"\n"
    else:
        logger.info("获取信息失败!")
        msg_all += "获取信息失败!"+"\n"
        return

    raw_personal_info = json.loads(get_personal_info.text)['datas']['wdqjbg']['rows'][0]
    raw_personal_info = get_info_2(sess, header, raw_personal_info["SQBH"])

    datas = {"QJLX_DISPLAY": "不涉及职能部门", "QJLX": "3bc0d68330fd4d869152238251b867ee", "DZQJSY_DISPLAY": "因事出校（当天往返）",
             "DZQJSY": "763ec35f8f5545c0aa245e8fbc20adb2", "QJXZ_DISPLAY": "因公", "QJXZ": "2", "QJFS_DISPLAY": "请假",
             "QJFS": "1", "YGLX_DISPLAY": "实验", "YGLX": "3", "SQSM": "", "QJKSRQ": "",
             "QJJSRQ": "", "QJTS": "1", "QJSY": "去无线谷", "ZMCL": "", "SJH": "",
             "DZSFLX_DISPLAY": "是", "DZSFLX": "1", "HDXQ_DISPLAY": "九龙湖校区", "HDXQ": "1", "DZSFLN_DISPLAY": "否",
             "DZSFLN": "0", "DZSFLKJSS_DISPLAY": "", "DZSFLKJSS": "", "DZ_SFCGJ_DISPLAY": "", "DZ_SFCGJ": "",
             "DZ_GJDQ_DISPLAY": "", "DZ_GJDQ": "", "QXSHEN_DISPLAY": "", "QXSHEN": "", "QXSHI_DISPLAY": "", "QXSHI": "",
             "QXQ_DISPLAY": "", "QXQ": "", "QXJD": "", "XXDZ": "无线谷", "JTGJ_DISPLAY": "", "JTGJ": "", "CCHBH": "",
             "SQBH": "", "XSBH": "", "JJLXR": "", "JJLXRDH": "",
             "JZXM": "", "JZLXDH": "", "DSXM": "", "DSDH": "", "FDYXM": "",
             "FDYDH": "", "SFDSQ": "0"}
    post_info = {}
    for key, value in datas.items():
        if key in raw_personal_info:
            if raw_personal_info[key] == 'null' or raw_personal_info[key] == None:
                post_info[key] = ''
            else:
                post_info[key] = raw_personal_info[key]
        else:
            post_info[key] = value
    if post_info['QJSY'] == '':
        post_info['QJSY'] = "去无线谷科研"
    post_info['SQBH'] = ''
    now_time = datetime.datetime.now()
    post_info["QJKSRQ"] = (now_time + datetime.timedelta(days=+1)).strftime("%Y-%m-%d 06:00")
    post_info["QJJSRQ"] = (now_time + datetime.timedelta(days=+1)).strftime("%Y-%m-%d 23:59")

    save_url = 'http://ehall.seu.edu.cn/ygfw/sys/xsqjappseuyangong/modules/leaveApply/addLeaveApply.do'
    header['Content-Type'] = 'application/x-www-form-urlencoded;charset=utf-8'
    FormData = {'data': post_info}
    data = parse.urlencode(FormData)

    save = sess.post(save_url, data=data, headers=header)

    if "成功" in save.text:
        logger.info("请假成功！")
        msg_all += "请假成功！"+"\n"
        return
    else:
        logger.info("请假失败！")
        msg_all += "请假失败！"+"\n"
        return


def report(sess, username):
    global msg_all
    province='江苏省'
    city='南京市'
    district='江宁区'
    LAT='31.88373374938965'
    LON='118.80831146240234'
    try:
        cookie_url = 'http://ehall.seu.edu.cn/qljfwapp2/sys/lwReportEpidemicSeu/configSet/noraml/getRouteConfig.do'
        header = get_wendu_header(sess, cookie_url)
        get_personal_info = get_wendu_info(sess, header)
        if get_personal_info.status_code == 403:
            raise
    except:
        cookie_url2 = 'http://ehall.seu.edu.cn/qljfwapp2/sys/itpub/common/changeAppRole/lwReportEpidemicSeu/20200223030326996.do'
        header = get_wendu_header(sess, cookie_url2)
        get_personal_info = get_wendu_info(sess, header)

    if get_personal_info.status_code == 200:
        logger.info('获取前一日信息成功!')
        msg_all += '获取前一日信息成功!'+"\n"
    else:
        logger.info("获取信息失败!")
        msg_all += '获取信息失败!'+"\n"
        return

    get_personal_info.encoding = 'utf-8'
    raw_personal_info = re.search('"rows":\[\{(.*?)}', get_personal_info.text).group(1)
    try:
        DZ_DQWZ = re.search('"DZ_DQWZ":"(.*?)"', raw_personal_info).group(1)
    except:
        DZ_DQWZ = ''
    raw_personal_info = json.loads('{' + raw_personal_info + '}')

    datas = "USER_ID=&PHONE_NUMBER=&IDCARD_NO=&GENDER_CODE=&DZ_MQSFWYSBL=&EMERGENCY_CONTACT_PERSON=&DZ_JQSTZK_DISPLAY=&DZ_ZHLKRQ=&REMARK=&EMERGENCY_CONTACT_NATIVE=&DZ_YXBMSFYSH_DISPLAY=&DZ_JRSFFS=&DZ_JTQY_DISPLAY=&DZ_GLJSSJ=&DZ_GLKSSJ=&EMERGENCY_CONTACT_HOME=&RYSFLB=&DZ_YSGLJZSJ=&DZ_YS_GLJZDCS_DISPLAY=&DZ_MQZNJWZ=&DZ_YWQTXGQK=&LOCATION_PROVINCE_CODE_DISPLAY=&DZ_SFDK=&HEALTH_STATUS_CODE=&DZ_DBRQ=&DZ_SFYJCS6_DISPLAY=&LOCATION_DETAIL=&DZ_WJZYMYY_DISPLAY=&DZ_SZWZLX=&DZ_SDXQ_DISPLAY=&DZ_JRSFYXC_DISPLAY=&DZ_DQWZ_QX=&DZ_DTWJTW=&DZ_JQSTZK=&DZ_WJZYMQTYY=&DZ_JJXFBD_CS_DISPLAY=&DZ_YS_GLJZDSF_DISPLAY=&DZ_WD=&DZ_SFYJCS10=&LOCATION_PROVINCE_CODE=&DZ_SZWZLX_DISPLAY=&HEALTH_STATUS_CODE_DISPLAY=&DZ_YXBMSFYSH=&DZ_SZWZ_GJ_DISPLAY=&DZ_SFYJCS8_DISPLAY=&BY6=&BY5=&DZ_SFLXBXS=&BY4=&BY3=&BY2=&DZ_YJZCDDGNRQ=&BY1=&DZ_JTFS=&DZ_QZ_GLJZDCS_DISPLAY=&DZ_MQSFWYSBL_DISPLAY=&DZ_JRSFYXC=&LOCATION_COUNTY_CODE=&DZ_SFYJCS2_DISPLAY=&DZ_QZ_GLJZDSF=&MENTAL_STATE=&DZ_SFDXBG=&IS_SEE_DOCTOR_DISPLAY=&BY14=&BY15=&BY12=&BY13=&BY18=&BY19=&BY16=&BY17=&DZ_XYYYPJG_DISPLAY=&DZ_DQWZ_JD=&BY10=&BY11=&DZ_JRSFFS_DISPLAY=&DZ_JRSTZK_DISPLAY=&CZR=&DZ_QZGLJZSJ=&DZ_YXBMCPQKSM=&DZ_SFYJCS9_DISPLAY=&CZZXM=&BY20=&HEALTH_UNSUAL_CODE_DISPLAY=&DZ_YMJZRQ1=&DZ_ZHJCGGRYSJ=&DZ_YMJZRQ2=&CLASS_CODE=&DZ_SYJTGJ_DISPLAY=&DZ_QZ_GLJZDCS=&DZ_SFGL=&DEPT_CODE=&CHECKED=&DZ_GLDQ=&CREATED_AT=&DZ_SFYJCS7_DISPLAY=&USER_NAME=&LOCATION_CITY_CODE=&BY7=&MEMBER_HEALTH_STATUS_CODE=&BY8=&BY9=&DZ_MDDSZSF_DISPLAY=&DZ_QZ_GLJZDSF_DISPLAY=&DZ_JCQKSM=&GENDER_CODE_DISPLAY=&DZ_SFYBH=&DZ_GLDCS=&DZ_GLDSF_DISPLAY=&DZ_GLDSF=&DZ_YXBMCPJG_DISPLAY=&DZ_SFYJCS10_DISPLAY=&DZ_DQWZ_WD=&DZ_DQWZ=&DZ_SFYJCS3_DISPLAY=&EMERGENCY_CONTACT_PHONE=&DZ_YS_GLJZDCS=&DZ_GLSZDQ=&DZ_MDDSZCS_DISPLAY=&DZ_JTFS_DISPLAY=&DZ_JRSTZK=&DZ_SFDXBG_DISPLAY=&DZ_SMJTQK=&DZ_WJZYMYY=&DZ_SFYSH_DISPLAY=&DZ_JJXFBSJ=&DZ_JSDTCJTW=&USER_NAME_EN=&DZ_SZXQ_DISPLAY=&DZ_JJXFBD_SF_DISPLAY=&DZ_MDDSZCS=&DZ_MDDSZSF=&MEMBER_HEALTH_UNSUAL_CODE=&DZ_CCBC=&DZ_SZWZ_GJ=&DZ_SFYBH_DISPLAY=&DZ_YS_GLJZDSF=&DZ_SFYSH=&IS_SEE_DOCTOR=&DZ_GLDQ_DISPLAY=&DZ_MQSFWQRBL=&CLASS=&MEMBER_HEALTH_STATUS_CODE_DISPLAY=&DZ_SFYJCS1_DISPLAY=&SAW_DOCTOR_DESC=&DZ_ZDYPJG_DISPLAY=&DZ_XYYSFYSH_DISPLAY=&DZ_ZHJCHZSJ=&DZ_ZZSM=&DZ_SFGL_DISPLAY=&DZ_DQWZ_SF=&DZ_GRYGLSJ1=&DZ_DTWSJCTW=&DZ_YWQTXGQK_DISPLAY=&DZ_GRYGLSJ2=&DZ_SFYJCS5_DISPLAY=&DZ_DQWZ_CS=&DZ_TWDS=&DZ_SZXQ=&DZ_XYYYPJG=&MENTAL_STATE_DISPLAY=&DZ_ZHJCGRYSJ1=&DZ_ZHJCGRYSJ2=&DZ_SYJTGJ=&HEALTH_UNSUAL_CODE=&DZ_XYYSFYSH=&CZRQ=&LOCATION_COUNTY_CODE_DISPLAY=&DZ_SFYJCS4=&DZ_SFYJCS3=&DZ_BRYWYXFH=&DZ_SFYJCS2=&DZ_SFYJCS1=&WID=&DZ_MQSFWQRBL_DISPLAY=&DEPT_NAME=&DZ_QKSM=&DZ_SFYJCS9=&DZ_SFYJCS8=&DZ_SFYJCS7=&DZ_SFYJCS6=&DZ_SFYJCS5=&DZ_BRYWYXFH_DISPLAY=&DZ_SDXQ=&LOCATION_CITY_CODE_DISPLAY=&DZ_SFLXBXS_DISPLAY=&DZ_ZDYPJG=&DZ_SZWZXX=&DZ_JJXFBD_CS=&DZ_JTQY=&MEMBER_HEALTH_UNSUAL_CODE_DISPLAY=&DZ_YXBMCPJG=&DZ_JJXFBD_SF=&DZ_SFYJCS4_DISPLAY=&DZ_GLDCS_DISPLAY=&DZ_YMJZD1=&NEED_CHECKIN_DATE=&DZ_YMJZD2="
    datas = parse_qs(datas, keep_blank_values=True)
    post_key = []
    for data in datas:
        post_key.append(data)

    post_info = {}
    for key in post_key:
        if key in raw_personal_info:
            if raw_personal_info[key] == 'null' or raw_personal_info[key] == None:
                post_info[key] = ''
            else:
                post_info[key] = raw_personal_info[key]
        else:
            post_info[key] = ''

    post_info['DZ_DQWZ'] = DZ_DQWZ
    post_info['DZ_SFYBH'] = '0'
    post_info['DZ_DBRQ'] = time.strftime("%Y-%m-%d", time.localtime())
    post_info['CREATED_AT'] = time.strftime("%Y-%m-%d %H:%M", time.localtime())
    post_info['NEED_CHECKIN_DATE'] = time.strftime("%Y-%m-%d", time.localtime())
    post_info['DZ_SFLXBXS'] = ''
    post_info['DZ_ZDYPJG'] = ''
    post_info['DZ_JSDTCJTW'] = '36.%d' % random.randint(0, 9)
    if district != '':
        post_info['DZ_DQWZ_WD'] = LON  # 经度, ,
        post_info['DZ_DQWZ'] = province + ', ' + city + ', ' + district
        post_info['DZ_DQWZ_QX'] = district
        post_info['DZ_DQWZ_SF'] = province
        post_info['DZ_DQWZ_CS'] = city
        post_info['DZ_DQWZ_JD'] = LAT  # 纬度
    save_url = 'http://ehall.seu.edu.cn/qljfwapp2/sys/lwReportEpidemicSeu/modules/dailyReport/T_REPORT_EPIDEMIC_CHECKIN_SAVE.do'
    save = sess.post(save_url, data=post_info, headers=header)
    if "您今日已提交过报平安" in save.text:
        logger.info('已打卡!')
        msg_all += "已打卡" + "\n"
    if save.status_code == 200:
        logger.info('打卡成功!')
        msg_all += "打卡成功"+"\n"
        return
    else:
        logger.info("打卡失败!")
        msg_all += "打卡失败"+"\n"
        return


def do_report(username, password, case):
    global msg_all
    sess = requests.session()

    if login(sess, username, password) == False:
        logger.info("登录失败！")
        msg_all += "登录失败！"+"\n"
        return

    logger.info("登录成功！")
    msg_all += "登录成功！"+"\n"

    if case=='1':
        logger.info("正在进行体温上报>>>>>>")
        msg_all += "正在进行体温上报>>>>>>"+"\n"
        report(sess, username)
        logger.info("正在进行请假>>>>>>")
        msg_all += "正在进行请假>>>>>>"+"\n"
        askForLeave(sess, username)
    elif case=='2':
        logger.info("正在进行体温上报>>>>>>")
        msg_all += "正在进行体温上报>>>>>>"+"\n"
        report(sess, username)
    elif case=='3': 
        logger.info("正在进行请假>>>>>>")
        msg_all += "正在进行请假>>>>>>"+"\n"
        askForLeave(sess, username)

    sess.close()
    return

 
if __name__ == '__main__':
    msg_all = ''
    logger.info("\n开始摸鱼行动\n")
    msg_all += "###开始摸鱼行动###"+"\n"
    sess = requests.session()
    if "ID_PSD_MODE" in os.environ:
        SEU_user_list = os.environ["ID_PSD_MODE"].split("&")
        for user_info in SEU_user_list:
            logger.info("--开始【"+user_info.split('——')[0]+"】--")
            msg_all += "--开始【"+user_info.split('——')[0]+"】--"+"\n"
            do_report(user_info.split('——')[0], user_info.split('——')[1].replace('@', '&'), user_info.split('——')[2])
    else:
        logger.info("读取环境变量失败")
        sys.exit()

    if "BARKKEY" in os.environ:
        back_key = os.environ["BARKKEY"]
    else:
        back_key = ""
    
    logger.info("msg_all = ", msg_all)
    logger.info("back_key = ", back_key)
    bark_post('摸鱼行动', msg_all, back_key)
