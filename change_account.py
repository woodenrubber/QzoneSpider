from selenium import webdriver
from urllib import request
from http import cookiejar
import json
import re
import redis
from yundama import identify

class InitialMessage(object):
    def __init__(self):
        self.rconn=redis.Redis('localhost',6379)
        self.readMyQQ()

    def readMyQQ(self,file_dir="./myqq.txt"):
        with open(file_dir,'r') as file:
            lines=file.readline()
            for line in lines:
                line=line.strip().replace(' ','--')
                cookie=InitialMessage.getCookies(qq=line.split('--')[0],password=line.split('--')[1])
                if(len(cookie>0)):
                    self.rconn.set(line,cookie,nx=True)#以["qq--password","cookies"]的形式存储在redis中

    #模拟登录并且获取当前登录账号的cookies
    def getCookies(qq,password,dama=False):
        driver=webdriver.Chrome()
        driver.get('http://qzone.qq.com')
        driver.switch_to_frame('login_frame')
        driver.find_element_by_id('switcher_plogin').click()
        driver.find_element_by_id('u').clear()
        driver.find_element_by_id('u').send_keys(qq)
        driver.find_element_by_id('p').clear()
        driver.find_element_by_id('p').send_keys(password)
        driver.find_element_by_id('login_button').click()

        while '验证码' in driver.page_source:
            try:
                print('需要处理验证码！')
                driver.save_screenshot('verification.png')
                if not dama:  # 如果不需要打码，则跳出循环
                    break
                iframes = driver.find_elements_by_tag_name('iframe')
                try:
                    driver.switch_to_frame(iframes[1])
                    input_verification_code = driver.find_element_by_id('cap_input')
                    submit = driver.find_element_by_id('verify_btn')
                    verification_code = identify()
                    print('验证码识别结果: %s' % verification_code)
                    input_verification_code.clear()
                    input_verification_code.send_keys(verification_code)
                    submit.click()
                except Exception:
                    break
            except Exception:
                return ''

        print(driver.title)
        cookie = {}
        for elem in driver.get_cookies():
            cookie[elem['name']] = elem['value']
        return json.dumps(cookie)  # 将字典转成字符串



