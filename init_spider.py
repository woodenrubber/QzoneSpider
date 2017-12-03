# coding=utf-8
import datetime #引入日期和时间包
import redis    #引入redis实例包以作为key-value操作


class InitSpider(object):
    # 设置爬虫参数，包括多线程的设置、QQ列表的设置、异常处理的设置等

    def __init__(self):
        # 初始化部分多线程参数
        self.myheader={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36',
                     'Referer': 'https://user.qzone.qq.com'}      #更改请求请求头信息，避免反爬虫生效,这里使用的是Mac OS + Chrome浏览器，根据不同的配置需要手动更改

        self.redis_connection=redis.Redis('localhost', 6379)    #连接redis存储系统,6379是默认端口
        # self.filter = Filter(self.redis_connection)     #对存储在redis内的数据进行去重操作

        self.thread_num_shuoshuo=4  # 4个线程实现说说爬取

        self.shuoshuo_after_date=datetime.datetime.strptime("2017-01-01","%Y-%m-%d")    #爬取2017年1月1日之后的说说

        self.read_QQ() #读取我的QQ列表
        self.wait_read_QQ() #等待爬取的QQ

        self.fail_time=2    #尝试2次网页请求失败即停止
        self.timeout=5      #请求超过5秒即为超时






