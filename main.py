import time
from selenium import webdriver
import requests
import re,pymongo
import json
import threading
import multiprocessing
from urllib import parse
import csv
import redis


#根据cookie得到GTK
def getGTK(cookie):
    hashes = 5381
    for letter in cookie['p_skey']:
        hashes += (hashes << 5) + ord(letter)
    return hashes & 0x7fffffff

#登录
def qqZoneLogin():
    driver = webdriver.Chrome('D:/chromedriver/chromedriver')
    driver.get('https://qzone.qq.com/')
    time.sleep(3)#弹出网页后，手动输入用户名和密码,时间长短自定。建议先登录QQ，可以直接快速登录，不用人工输入用户名和密码
    html=driver.page_source
    g_qzonetoken=re.search(r'window\.g_qzonetoken = \(function\(\)\{ try\{return (.*?);\} catch\(e\)',html)#从网页源码中提取g_qzonetoken
    #获取cookie
    cookies = driver.get_cookies()
    cookie={}
    for elem in driver.get_cookies():
        cookie[elem['name']] = elem['value']
    #计算gtk
    gtk=getGTK(cookie)#通过getGTK函数计算gtk
    return cookie,gtk,g_qzonetoken.group(1)

#获取说说数据
def getQQMoodMsg(qq,cookie,gtk,qzonetoken):
    errornum=0
    pos=0
    result=True
    shuolist = []
    shuo = dict()
    while result and errornum < 2:
        try:
            print(qq,'开始爬取说说')
            headers = {
                'Host': 'h5.qzone.qq.com',
                'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:53.0) Gecko/20100101 Firefox/53.0',
                'Accept': '*/*',
                'Accept-Language':'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
                'Accept-Encoding': 'gzip, deflate, br',
                'Referer': 'https://user.qzone.qq.com/790178228?_t_=0.22746974226377736',
                'Connection':'keep-alive'
            }
            params={
                    'uin':qq,
                    'inCharset':'utf-8',
                    'outCharset':'utf-8',
                    'hostUin':qq,
                    'notice':0,
                    'sort':0,
                    'pos':pos,
                    'num':20,
                    'cgi_host':'http://taotao.qq.com/cgi-bin/emotion_cgi_msglist_v6',
                    'code_version':'1',
                    'format':'jsonp',
                    'need_private_comment':'1',
                    'g_tk':gtk,
                    'qzonetoken':qzonetoken
                }
            html=s.request('GET','https://h5.qzone.qq.com/proxy/domain/taotao.qq.com/cgi-bin/emotion_cgi_msglist_v6',params=params,headers=headers,cookies=cookie)
            msgJson=json.loads(html.text.replace('_Callback(','').replace(');',''))
            if msgJson['code']==-10031:
                print('无权限访问')
                result=False
            elif msgJson['code']==0:
                if msgJson['usrinfo']['msgnum']==0:
                    print('该好友无说说数据！')
                    result=False
                else:
                    for msg in msgJson['msglist']:

                        shuo['qq'] = str(qq)
                        shuo['name'] = str(msg['name']).replace('\'','')
                        shuo['tid'] = str(msg['tid'])
                        shuo['pos_name'] = str(msg['lbs']['name']).replace('\'','')
                        shuo['source_name'] = str(msg['source_name']).replace('\'','')
                        time_local = time.localtime(msg['created_time'])
                        # 转换成新的时间格式(2016-05-05 20:28:54)
                        dt = time.strftime("%Y-%m-%d %H:%M:%S", time_local)
                        shuo['created_time'] = str(dt)
                        shuo['content'] = str(msg['content']).replace('\n','').replace('\'','')
                        shuo['cmtnum'] = msg['cmtnum']

                        shuolist.append(shuo.copy())

                    result = False
                    db['blog'].insert(shuolist)
                    print('爬取说说成功！')

            else:
                print('未知状态码，结束该QQ号数据抓取进程！')
                result=False

        except Exception as e:#输出异常，并尝试继续请求该页面
            print('发生错误了......',e)
            errornum+=1

    return shuolist


def getQQMsg(qq,cookie,gtk,qzonetoken):
    errornum=0
    result=True
    user = dict()
    hash_gender = {0: 'Unknown', 1: '男', 2: '女'}
    hash_marriage = {0: 'Unknown', 1: '单身', 2: '已婚', 3: '保密', 4: '恋爱中', 5: '已订婚', 6: '分居', 7: '离异'}
    while result and errornum < 2:
        try:
            print(qq,'爬取个人信息')
            headers = {
                'Host': 'h5.qzone.qq.com',
                'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:53.0) Gecko/20100101 Firefox/53.0',
                'Accept': '*/*',
                'Accept-Language':'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
                'Accept-Encoding': 'gzip, deflate, br',
                'Referer': 'https://user.qzone.qq.com/790178228?_t_=0.22746974226377736',
                'Connection':'keep-alive'
            }
            params = {
                "uin": qq,
                "fupdate": 1,
                "outCharset": 'utf-8',
                "g_tk": gtk,
            }
            html=s.request('GET','https://h5.qzone.qq.com/proxy/domain/base.qzone.qq.com/cgi-bin/user/cgi_userinfo_get_all?',params=params,headers=headers,cookies=cookie)
            msgJson=json.loads(html.text.replace('_Callback(','').replace(');',''))
            if msgJson['code']==-10031:
                print('无权限访问')
                result=False
            elif msgJson['code'] == -4009:
                print('无法访问该用户信息')
                result=False
            else:

                msg = msgJson['data']

                user['qq'] = str(qq)
                user['nickname'] = str(msg['nickname']).replace('\'', '')
                user['spacename'] = str(msg['spacename']).replace('\'', '')
                user['sex'] = hash_gender[int(str(msg['sex']))]
                user['age'] = str(msg['age'])
                user['birthyear'] = str(msg['birthyear']).replace('\'', '')
                user['birthday'] = str(msg['birthday']).replace('\'', '')
                user['country'] = str(msg['country']).replace('\'', '')
                user['province'] = str(msg['province']).replace('\'', '')
                user['city'] = str(msg['city'])
                user['marriage'] = hash_marriage[int(str(msg['marriage']))]
                result = False
                db['user'].insert(user)
                print('爬取个人信息成功！')

        except Exception as e:#输出异常，并尝试继续请求该页面
            print('发生错误了......',e)
            errornum+=1

        time.sleep(2)
    return user

def getQQFriend(qq,cookie,gtk,qzonetoken):
    errornum=0
    result=True
    friend = dict()
    friendlist = []
    i = 0

    while result and errornum < 2:
        try:
            print(qq,' :爬取最近访客信息')
            headers = {
                'Host': 'h5.qzone.qq.com',
                'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:53.0) Gecko/20100101 Firefox/53.0',
                'Accept': '*/*',
                'Accept-Language':'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
                'Accept-Encoding': 'gzip, deflate, br',
                'Referer': 'https://user.qzone.qq.com/790178228?_t_=0.22746974226377736',
                'Connection':'keep-alive'
            }
            params = {
                "uin": qq,
                "mask": 2,
                "mod": 2,
                "fupdate": 1,
                "qzonetoken": qzonetoken,
                "g_tk": gtk,
            }
            html=s.request('GET','https://user.qzone.qq.com/proxy/domain/g.qzone.qq.com/cgi-bin/friendshow/cgi_get_visitor_simple?',params=params,headers=headers,cookies=cookie)
            msgJson=json.loads(html.text.replace('_Callback(','').replace(');',''))

            if msgJson['code']==-10031:
                print('无权限访问')
                result=False
            elif msgJson['code'] == -99996:
                print('该用户关闭了访客查看')
                result=False
            else:
                msg = msgJson['data']['items']
                # print(msg)
                for item in msg:

                    friend['uin'] = str(qq)
                    friend['name'] = str(item['name']).replace('\'', '')
                    friend['qq'] = str(item['uin'])
                    time_local = time.localtime(item['time'])
                    # 转换成新的时间格式(2016-05-05 20:28:54)
                    dt = time.strftime("%Y-%m-%d %H:%M:%S", time_local)
                    friend['time'] = str(dt)
                    friend['qzone_level'] = item['qzone_level']

                    if not isContains(str(item['uin'])):  # 先去重
                        qq_insert(str(item['uin']))
                        rcon.lpush('QQZone:QQlist', str(item['uin']))
                        print('+1')

                    friendlist.append(friend.copy())

                    i = i + 1
                    if i > 10:
                        break

                result = False
                db['friend'].insert(friendlist)
                print('爬取访客信息成功！')

        except Exception as e:#输出异常，并尝试继续请求该页面
            print('发生错误了......',e)
            errornum+=1

        time.sleep(2)
    return friendlist

# 构造点赞的人的URL
def get_aggree_url(self):
    url = 'https://user.qzone.qq.com/proxy/domain/g.qzone.qq.com/cgi-bin/friendshow/cgi_get_visitor_simple?uin=QQ号&mask=2&mod=2&fupdate=1&g_tk=121307362&qzonetoken=694e991fd4ee1f360edf1c18c63b2bd6fbb61be931b1a34b3c5b8ac5d27c372537f12f625db554f3&g_tk=121307362'
    params = {
        "uin": qq,
        "mask": 2,
        "mod": 2,
        "fupdate": 1,
        "qzonetoken": qzonetoken,
        "g_tk":gtk,
    }
    url = url + parse.urlencode(params)
    return url



def isContains(str_input):
    str_input = int(str_input)
    return rcon.getbit('QQZone:QQbit', str_input) if (0 < str_input) and (str_input < 4500000000) else 1

def qq_insert(str_input):
    str_input = int(str_input)
    if (0 < str_input) and (str_input < 4500000000):
        rcon.setbit('QQZone:QQbit', str_input, 1)

if __name__ == '__main__':
    db = pymongo.MongoClient('localhost', 27017)['QQZone1']
    shuoshuo = db['friend']
    rcon = redis.Redis('localhost', 6379, decode_responses=True)
    cookie,gtk,qzonetoken=qqZoneLogin()#登录
    s=requests.session()#用requests初始化会话
    qqlist=[543419609]

    with open("QQmail.csv", "r", encoding="utf-8") as csvfile:
        # 读取csv文件，返回的是迭代类型
        read = csv.reader(csvfile)
        for qq in read:
            qqlist.append(qq[0])
            if not isContains(qq[0]):  # 先去重
                qq_insert(qq[0])
                rcon.lpush('QQZone:QQlist', qq[0])
    print('初始QQ数: %s' % rcon.llen('QQZone:QQlist'))

    print(rcon.rpop('QQZone:QQlist'))

    number_qq = rcon.llen('QQZone:QQlist')

    while number_qq > 0:

        qq = rcon.rpop('QQZone:QQlist')

        getQQMoodMsg(qq, cookie, gtk, qzonetoken)
        getQQMsg(qq, cookie, gtk, qzonetoken)
        getQQFriend(qq, cookie, gtk, qzonetoken)

        number_qq = rcon.llen('QQZone:QQlist')
        print(number_qq)

