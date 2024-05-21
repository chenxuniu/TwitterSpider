import selenium
from selenium import webdriver
import platform,sys,os,time
from selenium_stealth import stealth
# from .chrome_plugins.extension import proxies
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

from selenium.webdriver.chrome.service import Service



class Browser:
    def __init__(self, proxy = None,
                 headless=False,version="114",ban_image_and_css=False,use_cap=False,debug_address = "",
                 *args,**kwargs):
        '''
        debug_address 用于连接已有的浏览器："127.0.0.1:9222"
        浏览器启动命令 chrome.exe --remote-debugging-port=9222 --user-data-dir="C:\selenium\ChromeProfile" --proxy-server=socks://127.0.0.1:10808
        proxy 支持两种传参形式
        (username, password, endpoint, port) # 使用需要用户名密码的代理
        "ip:port"或者http(s)://ip:port   使用代理
        '''
        #### insert your own chromedriver
        # driver_location = "./chromedriver_win32_for_chrome_version_118/chromedriver"
        driver_location = "/opt/homebrew/bin/chromedriver"

        if not os.path.exists(driver_location):
            print("where is your perled driver?!")
            sys.exit(0)
        else:
            print("[++++++++++++++++++++++++++++Use Baseclass++++++++++++++++++++++++++++++++++]")
        if debug_address!="":
            print("[+]请使用命令启动Chrome:{}".format('chrome.exe --remote-debugging-port=9222 --user-data-dir="C:\selenium\ChromeProfile" --proxy-server=socks://127.0.0.1:10808'))
            options = webdriver.ChromeOptions()
            # options.add_experimental_option("debuggerAddress", debug_address)
            # self.driver = webdriver.Chrome(options=options, executable_path=driver_location) # 会等待debug_address浏览器启动
            service = Service(executable_path=driver_location)
            options.add_experimental_option("debuggerAddress", debug_address)
            self.driver = webdriver.Chrome(options=options, service=service)  # 会等待debug_address浏览器启动
        else:

            options = webdriver.ChromeOptions()
            # options.add_argument("start-maximized")
            # 关闭自动测试状态显示 // 会导致浏览器报：请停用开发者模式xv./、c/c。。，
            options.add_experimental_option("useAutomationExtension", False)
            options.add_argument('--disable-blink-features=AutomationControlled')
            # options.add_argument('--ignore-certificate-errors')
            # 部署项目在linux时，其驱动会要求这个参数 不然会报错
            if 'Windows' not in platform.platform():
                options.add_argument('--no-sandbox')
                options.add_argument('--disable-gpu')
            # 禁止用户名密码弹窗
            prefs = {}

            prefs["credentials_enable_service"] = False
            prefs["profile.password_manager_enabled"] = False
            # 禁用图片加载和CSS
            if ban_image_and_css:
                prefs["profile.managed_default_content_settings.images"] = 2
                prefs["permissions.default.stylesheet"] = 2
            options.add_experimental_option("prefs", prefs)
            if proxy!= None:
                print("接收到代理参数:",proxy)
                if isinstance(proxy,tuple):
                    # 需要用户名和密码验证的代理
                    proxies_extension = proxies(*proxy)  # 插件形式
                    options.add_extension(proxies_extension)
                elif isinstance(proxy,str):
                    if "://" in proxy:
                        options.add_argument('--proxy-server={}'.format(proxy))
                    else:
                        options.add_argument('--proxy-server={}'.format('http://' + proxy))
            if headless:
                options.add_argument("--headless")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            # options.add_experimental_option('useAutomationExtension', False)
            # options.add_experimental_option('mobileEmulation', {'deviceName': 'Nexus 5'})
            # 开启流量监听
            # https://stackoverflow.com/questions/20907180/getting-console-log-output-from-chrome-with-selenium-python-api-bindings
            # https://blog.csdn.net/weixin_46279624/article/details/128405076
            # 目前有些流量抓不到 看能不能参考上述链接解决
            self.use_cap = use_cap
            if use_cap:
                caps = DesiredCapabilities.CHROME
                caps['goog:loggingPrefs'] = {'performance': 'ALL'}

            else:
                caps = None

            print(driver_location)
            self.driver = webdriver.Chrome(options=options,
                                           executable_path=driver_location,
                                           desired_capabilities=caps)
            self.driver.set_window_size(800, 600)

