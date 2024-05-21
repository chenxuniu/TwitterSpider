from selenium import webdriver
import time, os, sys
import selenium
import platform
import datetime
import json
import subprocess
from typing import List, Dict

from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

def createCOC(browser):
    class COC(browser):
        def __init__(self, *args,**kwargs):
            super(COC, self).__init__(*args,**kwargs)
            '''
            proxy 支持两种传参形式
            (username, password, endpoint, port) # 使用需要用户名密码的代理
            "ip:port"或者http(s)://ip:port   使用代理
            '''
            self.pause = lambda x: time.sleep(0.001 * random.randint(max(0, x * 1000 - 1500), x * 1000 + 1500))
            self.action = ActionChains(self.driver)
            self.possible_obstacle_pool = []
            self.history_traffic = [] # 因为driver.get_log('performance')每次读取都是从上一次调用的流量后接着

        def debug_pause(self):
            while True:
                command = input(">>> ") #
                if command == "exit":
                    break
                try:
                    result = exec(command)  # eval只允许表达式，exec功能更全面
                    if result is not None:
                        print(result)
                except Exception as e:
                    print("[-]Error:", e)

        def save_traffic(self,save_file):
            if not self.use_cap:
                print("[-]Please set use_cap to True")
                return
            for entry in self.driver.get_log('performance'):
                self.history_traffic.append(entry)
            if os.path.exists(save_file):
                i = 1
                new_file = save_file + f".{i}"
                while os.path.exists(new_file):
                    i += 1
                    new_file = save_file + f".{i}"
                print("[!]{}文件存在，所有流量保存为{}，并清空get_log('performance')".format(save_file, new_file))
                save_file = new_file
            else:
                print("[+]所有流量保存为{}，并清空get_log('performance')".format(save_file))
            with open(save_file,"w") as f:
                for entry in self.history_traffic:
                    f.write(str(entry) + "\n")

        def get_cookies(self):
            '''[{'domain': 'rendezvousparis.hermes.com', 'expiry': 1681364100, 'httpOnly': True, 'name': 'app.sig', 'path': '/', 'sameSite': 'Lax', 'secure': True, 'value': '_Le9PhGcuXlieaThOlRNk8NKrw0'},
             {'domain': 'rendezvousparis.hermes.com', 'expiry': 1712813702, 'httpOnly': False, 'name': 'policy', 'path': '/', 'sameSite': 'Lax', 'secure': False, 'value': 'accepted'}'''
            return self.driver.get_cookies()

        def get_request_api_ua(self,url_api):
            result = self.get_request_api_headers(url_api,just_one_result=True)
            try:
                return result[0]['header_dict']['User-Agent']
            except IndexError:
                print("[-]IndexError")
                print(result)
                return ""
            except KeyError:
                print("[-]KeyError")
                print(result[0])
                return ""

        def get_request_api_anyheader(self,url_api,header_name="Cookie"):
            # header_name常用设置有：Authorization
            result = self.get_request_api_headers(url_api,just_one_result=True)
            try:
                return result[0]['header_dict'][header_name]
            except IndexError:
                print("[-]IndexError")
                print(result)
                return ""
            except KeyError:
                print("[-]KeyError")
                print(result[0])
                return ""

        def get_request_api_headers(self, url_api, url_handle=lambda x:x.split("?")[0],just_one_result=False):
            # 默认匹配规则是不考虑请求的参数，只要路径一致即可，lambda x:x.split("?")[0]
            # url_api最好是完整路径http(s)://xxx/x/xx
            # 只能得到header得不到cookie
            if not self.use_cap:
                print("[-]Please set use_cap to True")
                return
            result: List[Dict] = []
            # 获取所有HTTP请求和响应的信息，并筛选出HTTP头信息,并且只包括非基本的头
            for entry in self.driver.get_log('performance'):
                self.history_traffic.append(entry)
                # print(json.loads(entry.get('message', {})))  # 如果发现抓不到请求可以打开这一行
                message = json.loads(entry.get('message', {})).get('message', {})
                # 判断消息是否为网络请求
                if message.get('method') == 'Network.requestWillBeSent':
                    if message.get('params', {}).get("documentURL", "") != "":
                        # documentURL 指的是页面的URL，而页面发起的JS请求应该判断url值
                        # document_url = message.get('params', {}).get("documentURL","")
                        url = message.get('params', {}).get("request", {}).get("url", "")
                        if url == "":
                            print("[-]get_request_api_headers没有提取到请求的完整路径:{}".format(entry))
                            continue
                        if url_handle(url) == url_api:
                            request_headers = message.get('params', {}).get('request', {}).get('headers')
                            if request_headers:
                                one_result = {
                                    'intact_url':url,
                                    'header_dict':request_headers
                                }
                                result.append(one_result)
                                if just_one_result:
                                    break
                            else:
                                print("[-]无法在指定的{}接口下发现任何header,该流量为:\n{}\n".format(url_api, entry))
            return result

        # 追求效率的简单点击操作
        def simple_click(self,x_path,wtime=2):
            WebDriverWait(self.driver, wtime).until(EC.element_to_be_clickable((By.XPATH, x_path))).click()
        def simple_input(self,x_path,input_data,wtime=2):
            t = WebDriverWait(self.driver, wtime).until(EC.element_to_be_clickable((By.XPATH, x_path)))
            t.send_keys(input_data)

        # 倾向于要点击成功的click逻辑
        def click(self, x_path):
            self.pause(4)
            print("execute click...")
            t = WebDriverWait(self.driver, 15).until(EC.element_to_be_clickable((By.XPATH, x_path)))
            try:
                t.click()
            except selenium.common.exceptions.StaleElementReferenceException:
                time.sleep(5)
                try:
                    t.click()
                except selenium.common.exceptions.StaleElementReferenceException as e:
                    raise e
            return 1

        # 倾向于要输入成功的input逻辑
        def input(self, x_path, input_data):
            self.pause(3)
            print("execute input {}...".format(input_data))
            try:
                # 弹窗不会阻碍presence_of_element_located
                t = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, x_path)))
            except selenium.common.exceptions.TimeoutException as e:
                raise e
            t.send_keys(input_data)
            t.clear()
            time.sleep(0.5)
            t.send_keys(input_data)
            return 1

        def check_obstacle(self):
            for func, param in self.possible_obstacle_pool:
                if func(*param) == True:
                    return True
            return False

        def set_obstacle(self, func, param):
            assert callable(func)
            assert isinstance(param, list)
            self.possible_obstacle_pool.append([func, param])

        def execute_with_ob(self, func, param):
            assert callable(func)
            assert isinstance(param, list)
            for i in range(2):
                try:
                    func(*param)
                except Exception as e:
                    if self.check_obstacle() == True:
                        print("遇到障碍，已经解决")
                        continue
                    else:
                        raise e
                else:
                    break

        def quit(self):
            self.driver.quit()
            try:
                self.closeBrowser() #关闭一些第三方浏览器
            except AttributeError:
                pass

    return COC

def test_get_cookie_header():
    from lib.AdsPowerHandler import AdsPowerHandler
    from BrowserModule.AdsPowerClass import Browser
    def createTaskClass(COC):
        class Hermes(COC):
            def __init__(self, use_cap=True, ads_id=None, clear_cache=0):
                super(Hermes, self).__init__(use_cap=use_cap, ads_id=ads_id,clear_cache=clear_cache)
        return Hermes
    aph = AdsPowerHandler()
    user_id = aph.addAccount()
    b = createTaskClass(createCOC(Browser))(ads_id=user_id, use_cap=True)
    b.driver.get("https://rendezvousparis.hermes.com/client/welcome")
    print(b.get_request_api_headers("https://rendezvousparis.hermes.com/client/welcome"))
    b.save_traffic("test.log")
    print(b.get_cookies())

if __name__ == '__main__':
    pass