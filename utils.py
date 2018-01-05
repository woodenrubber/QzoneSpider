import time
from selenium import webdriver
import re



#根据cookie得到GTK
def getGTK(cookie):
    hashes = 5381
    for letter in cookie['p_skey']:
        hashes += (hashes << 5) + ord(letter)
    return hashes & 0x7fffffff

#模拟登录
def qqZoneLogin():
    driver = webdriver.Chrome('D:/chromedriver/chromedriver')
    driver.get('https://qzone.qq.com/')
    time.sleep(5)#弹出网页后，手动输入用户名和密码,时间长短自定。建议先登录QQ，可以直接快速登录，不用人工输入用户名和密码
    # 模拟登陆成功
    html=driver.page_source
    g_qzonetoken=re.search(r'window\.g_qzonetoken = \(function\(\)\{ try\{return (.*?);\} catch\(e\)',html)#从网页源码中提取g_qzonetoken
    #获取cookie
    cookies = driver.get_cookies()
    cookie={}
    for elem in driver.get_cookies():
        cookie[elem['name']] = elem['value']
    #计算gtk
    gtk=getGTK(cookie)#通过getGTK函数计算gtk
    driver.quit()
    return cookie,gtk,g_qzonetoken.group(1)
