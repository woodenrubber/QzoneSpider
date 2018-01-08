import time
import requests
import pymongo
import json
import csv
import redis
import random
from utils import qqZoneLogin
from utils import USER_AGENT_LIST

def zone_spider():


    user_agent = random.choice(USER_AGENT_LIST)
    headers = {
        'host': 'h5.qzone.qq.com',
        'accept-encoding': 'gzip, deflate, br',
        'accept-language': 'zh-CN,zh;q=0.8',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'user-agent': user_agent,
        'connection': 'keep-alive'
    }

    proxie = {
        'http': 'http://113.221.46.180:8888'
    }

    file = open('proxy.txt', mode='r', encoding='UTF-8')
    iplist = file.read()
    proxies = iplist.split()
    ip = random.choice(proxies)
    proxie['http'] = 'http://%s'% ip
    print(proxie)
    # 连接mongodb数据库，用来储存QQ空间信息
    db = pymongo.MongoClient('localhost', 27017)['QQZone1']

    # 连接redis数据库，用来存储待爬QQ号
    rcon = redis.Redis('localhost', 6379, decode_responses=True)

    # 模拟登录
    cookie, gtk, qzonetoken = qqZoneLogin()

    # 用requests初始化会话
    s = requests.session()

    # 获取用户说说数据
    def getQQMoodMsg(qq, cookie, gtk, qzonetoken):
        errornum = 0
        pos = 0
        result = True
        shuolist = [] # 存储20个说说的列表
        shuo = dict() # 存储1个说说的字典

        while result and errornum < 2:
            try:
                print(qq, '开始爬取说说')

                # 构建请求的参数值和完整的url
                params = {
                    'uin': qq,
                    'inCharset': 'utf-8',
                    'outCharset': 'utf-8',
                    'hostUin': qq,
                    'notice': 0,
                    'sort': 0,
                    'pos': pos,
                    'num': 20,
                    'cgi_host': 'http://taotao.qq.com/cgi-bin/emotion_cgi_msglist_v6',
                    'code_version': '1',
                    'format': 'jsonp',
                    'need_private_comment': '1',
                    'g_tk': gtk,
                    'qzonetoken': qzonetoken
                }
                html = s.request('GET',
                                 'https://h5.qzone.qq.com/proxy/domain/taotao.qq.com/cgi-bin/emotion_cgi_msglist_v6',
                                 params=params, headers=headers, cookies=cookie)
                # 获得请求返回的json包
                msgJson = json.loads(html.text.replace('_Callback(', '').replace(');', ''))

                # 分析返回包的代码，判断是否有权限访问或其他错误
                if msgJson['code'] == -10031:
                    print('无权限访问')
                    result = False
                elif msgJson['code'] == 0:

                    if msgJson['usrinfo']['msgnum'] == 0:
                        print('该好友无说说数据！')
                        result = False
                    else:
                        for msg in msgJson['msglist']:
                            # 解析json包，获取说说相关信息
                            shuo['qq'] = str(qq)
                            shuo['name'] = str(msg['name']).replace('\'', '')
                            shuo['tid'] = str(msg['tid'])
                            shuo['pos_name'] = str(msg['lbs']['name']).replace('\'', '')
                            shuo['source_name'] = str(msg['source_name']).replace('\'', '')
                            time_local = time.localtime(msg['created_time'])
                            # 转换成新的时间格式(2016-05-05 20:28:54)
                            dt = time.strftime("%Y-%m-%d %H:%M:%S", time_local)
                            shuo['created_time'] = str(dt)
                            shuo['content'] = str(msg['content']).replace('\n', '').replace('\'', '')
                            shuo['cmtnum'] = msg['cmtnum']
                            # 存入列表中
                            shuolist.append(shuo.copy())

                        result = False
                        db['blog'].insert(shuolist) # 插入数据库中
                        print('爬取说说成功！')

                else:
                    print('未知状态码，结束该QQ号数据抓取进程！')
                    result = False

            except Exception as e:  # 输出异常，并尝试继续请求该页面
                print('发生错误了......', e)
                errornum += 1

        return shuolist

    def getQQMsg(qq, cookie, gtk):
        errornum = 0
        result = True
        user = dict()
        # 对信息表中的字段信息扩展
        hash_gender = {0: 'Unknown', 1: '男', 2: '女'}
        hash_marriage = {0: 'Unknown', 1: '单身', 2: '已婚', 3: '保密', 4: '恋爱中', 5: '已订婚', 6: '分居', 7: '离异'}
        while result and errornum < 2:
            try:
                print(qq, '爬取个人信息')
                #构建请求的参数和完整的url
                params = {
                    "uin": qq,
                    "fupdate": 1,
                    "outCharset": 'utf-8',
                    "g_tk": gtk,
                }
                html = s.request('GET',
                                 'https://h5.qzone.qq.com/proxy/domain/base.qzone.qq.com/cgi-bin/user/cgi_userinfo_get_all?',
                                 params=params, headers=headers, cookies=cookie)
                # 获取返回的json包
                msgJson = json.loads(html.text.replace('_Callback(', '').replace(');', ''))
                if msgJson['code'] == -10031:
                    print('无权限访问')
                    result = False
                elif msgJson['code'] == -4009:
                    print('无法访问该用户信息')
                    result = False
                else:
                    # 解析包含用户信息的数据
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
                    db['user'].insert(user) # 插入数据库
                    print('爬取个人信息成功！')

            except Exception as e:  # 输出异常，并尝试继续请求该页面
                print('发生错误了......', e)
                errornum += 1

            time.sleep(2)
        return user

    def getQQFriend(qq, cookie, gtk, qzonetoken):
        errornum = 0
        result = True
        friend = dict() #保存单个访问好友的信息
        friendlist = [] #访问好友信息的列表
        i = 0

        while result and errornum < 2:
            try:
                print(qq, ' :爬取最近访客信息')
                #构建请求参数和完整url
                params = {
                    "uin": qq,
                    "mask": 2,
                    "mod": 2,
                    "fupdate": 1,
                    "qzonetoken": qzonetoken,
                    "g_tk": gtk,
                }
                html = s.request('GET',
                                 'https://user.qzone.qq.com/proxy/domain/g.qzone.qq.com/cgi-bin/friendshow/cgi_get_visitor_simple?',
                                 params=params, headers=headers, cookies=cookie)
                # 返回json包
                msgJson = json.loads(html.text.replace('_Callback(', '').replace(');', ''))

                if msgJson['code'] == -10031:
                    print('无权限访问')
                    result = False
                elif msgJson['code'] == -99996 or msgJson['code'] == -4016:
                    print('该用户关闭了访客查看')
                    result = False
                else:
                    msg = msgJson['data']['items']
                    # 解析访客信息
                    for item in msg:

                        friend['uin'] = str(qq)
                        friend['name'] = str(item['name']).replace('\'', '')
                        friend['qq'] = str(item['uin'])
                        time_local = time.localtime(item['time'])
                        # 转换成新的时间格式(2016-05-05 20:28:54)
                        dt = time.strftime("%Y-%m-%d %H:%M:%S", time_local)
                        friend['time'] = str(dt)
                        friend['qzone_level'] = item['qzone_level']
                        # 将访客的qq号加入待爬的QQ队列中
                        if not isContains(str(item['uin'])):  # 先去重
                            qq_insert(str(item['uin']))
                            rcon.lpush('QQZone:QQlist', str(item['uin']))
                            print('+1')


                        # 只访问前10个访客
                        i = i + 1
                        if i < 11:
                            friendlist.append(friend.copy())


                    result = False
                    db['friend'].insert(friendlist) # 插入数据库中
                    print('爬取访客信息成功！')

            except Exception as e:  # 输出异常，并尝试继续请求该页面
                print('发生错误了......', e)
                errornum += 1

            time.sleep(2)
        return friendlist

    #******去重处理参考了LiuXingMing的方法，github地址：https://github.com/LiuXingMing/QQSpider***********
    # 判断是否在redis记录中
    def isContains(str_input):
        str_input = int(str_input)
        return rcon.getbit('QQZone:QQbit', str_input) if (0 < str_input) and (str_input < 4500000000) else 1
    # 插入相应的qq位信息
    def qq_insert(str_input):
        str_input = int(str_input)
        if (0 < str_input) and (str_input < 4500000000):
            rcon.setbit('QQZone:QQbit', str_input, 1)
    #****************************************************************************************************

    #读取待爬的QQ数
    number_qq = rcon.llen('QQZone:QQlist')
    finish_qq = db['user'].count()


    #初始待爬qq列表
    with open("QQmail.csv", "r", encoding="utf-8") as csvfile:
        # 读取csv文件，返回的是迭代类型
        read = csv.reader(csvfile)
        for qq in read:

            if not isContains(qq[0]):  # 先去重
                qq_insert(qq[0])
                rcon.lpush('QQZone:QQlist', qq[0])
    print('初始QQ数: %s' % rcon.llen('QQZone:QQlist'))

    while number_qq > 0 or finish_qq < 10000:
        # 取出redis中的待爬qq
        qq = rcon.rpop('QQZone:QQlist')

        # 爬取QQ空间信息
        getQQMoodMsg(qq, cookie, gtk, qzonetoken)
        getQQMsg(qq, cookie, gtk)
        getQQFriend(qq, cookie, gtk, qzonetoken)

        # 再次读取待爬qq数
        number_qq = rcon.llen('QQZone:QQlist')
        finish_qq = db['user'].count()
        print('待爬取的QQ数： ',number_qq)
        print('已爬取成功的QQ数： ',finish_qq)

