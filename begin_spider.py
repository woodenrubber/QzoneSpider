import time
import threading
import multiprocessing

import redis
from QQzone_spider import zone_spider


# 开启多线程爬虫
def thread_spider():
    max_threads = 4
    threads = []
    SLEEP_TIME = 2
    # 获取待爬取的QQ数目，存储在redis中
    rcon = redis.Redis('localhost', 6379, decode_responses=True)
    number_qq = rcon.llen('QQZone:QQlist')
    while threads or number_qq > 0:# 当线程池至少存在一个线程或者待爬数目大于0时
        for thread in threads:
            if not thread.is_alive():# 对于死掉的线程，直接销毁
                threads.remove(thread)
        while len(threads) < max_threads: # 实时增加线程，直到达到最大数目
            thread = threading.Thread(target=zone_spider)
            print("启动线程")
            thread.setDaemon(True)
            thread.start()
            threads.append(thread)
        time.sleep(SLEEP_TIME)

# def process_spider():
#     process = []
#     num_cpus = multiprocessing.cpu_count()
#     print('启动进程数： ',num_cpus)
#     for i in range(num_cpus):
#         p = multiprocessing.Process(target=thread_spider)
#         p.start()
#         process.append(p)
#     for p in process:
#         p.join()

if __name__ == "__main__":
    thread_spider()