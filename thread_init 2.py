from init_spider import InitSpider
import threading
import time

class MyThread(threading.Thread):               #创建多线程函数
    def __init__(self):
        super(MyThread, self).__init__()

    def run(self):
        time.sleep(1)
        InitSpider()  # 每个线程分别运行初始化函数

for i in range(4):    #每个线程依次开始运行
    t=MyThread(i)
    t.start