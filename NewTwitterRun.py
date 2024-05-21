import sys
from loguru import logger
import datetime
import random
import string
from TwitterSpiderLogic import createTaskClass
from mylib.CommonOperationClass import createCOC
from BrowserModule.BaseClass import Browser
from AccountManager import AccountManager

"""
需要修改的配置参数放到了main的前几排
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222 --user-data-dir="/Users/xuchen/Desktop/Python_code/ChromeProfile"
"""

logger.add("runtime.log")       # 创建了一个文件名为runtime的log文件

def generate_random_string(seed,length=5):
    random.seed(int(seed))
    letters = string.ascii_letters
    random_string = ''.join(random.choice(letters) for i in range(length))
    return random_string

def LoadUrlData(filename):
    url_list = []
    with open(filename) as f:
        for line in f.readlines()[1:]:
            numId = line.split(",")[0]
            url_list.append("https://twitter.com/{}/status/{}".format(generate_random_string(int(numId),5),numId))
    return url_list


def LoadUrl(filename):
    url_list = []
    with open(filename) as f:
        for line in f.readlines()[1:]:
            numId = line.split("\n")[0]
            url_list.append("https://twitter.com/{}/status/{}".format(generate_random_string(int(numId),5),numId))
    # print(url_list)
    return url_list

def GetNewBrowser():
    try:
        # debug
        b = createTaskClass(createCOC(browser=Browser))(headless=False,
                                                            # proxy="socks5://127.0.0.1:10808",
                                                            debug_address="127.0.0.1:9222",version="118")
    except Exception as e:
        logger.error(str(e))
        sys.exit()
    return b

# mm...this page doesn’t exist. Try searching for something else.
"""
index_id测试样例
1是比较简单的测试show more replies评论的
8测试first reply
"""
def main():
    max_spider_comments = 500 # 每个URL最多提取多少评论条数
    account_manager = AccountManager(filename="account.csv")
    url_list = LoadUrl(filename="twitter_5000.csv") # DataManager需要管理是否成功被提取
    print(url_list)
    index_id = 1353
    need_new_browser = True
    b,email,pw,uname = None,None,None,None
    max_error = 5 # 如果连续出现五次抓取报错，程序退出，请调试程序
    error = 0

    while index_id < len(url_list):

        print("正在尝试提取序号为{}的内容，从0开始".format(index_id))
        url = url_list[index_id]
        if need_new_browser:
            b = GetNewBrowser()
            email,pw,uname = account_manager.getAccount()
            try:
                print("try to load url.....")
                if b.run(url, email, pw, uname, max_spider_comments,index_id):
                    print("loading.....")
                    logger.info("[+]Extract contents from {} successfully".format(url.split("/")[-1]))
                    # 调试的时候开启的
                    if do_debug:
                        while True:
                            command = input(">>> ")  #
                            if command == "exit":
                                break
                            try:
                                result = exec(command)  # eval只允许表达式，exec功能更全面
                                if result is not None:
                                    print(result)
                            except Exception as e:
                                print("[-]Error:", e)
                else:
                    need_new_browser = True
                    b.quit()
                    account_manager.markAccountAsBlock(email)
                error = 0
            except Exception as e:
                logger.error(f"{email},{pw},{uname},{url}\n"+"-"*50 +"\n"+str(e).strip()+"\n"+"-"*50 + "\n")
                need_new_browser = True
                b.quit()
                error += 1
                if error > max_error:
                    sys.exit()

            # 判读是否没有可用账户
            if email == None:
                logger.error("[-]All accounts are blocked!!!")
                sys.exit(0)
            # need_new_browser = False
        index_id = index_id+1

        # try:
        #     print("try to load url.....")
        #     if b.run(url, email, pw, uname, max_spider_comments,index_id):
        #         print("loading.....")
        #         index_id += 1
        #         logger.info("[+]Extract contents from {} successfully".format(url.split("/")[-1]))
        #         # 调试的时候开启的
        #         if do_debug:
        #             while True:
        #                 command = input(">>> ")  #
        #                 if command == "exit":
        #                     break
        #                 try:
        #                     result = exec(command)  # eval只允许表达式，exec功能更全面
        #                     if result is not None:
        #                         print(result)
        #                 except Exception as e:
        #                     print("[-]Error:", e)
        #     else:
        #         need_new_browser = True
        #         b.quit()
        #         account_manager.markAccountAsBlock(email)
        #     error = 0
        # except Exception as e:
        #     logger.error(f"{email},{pw},{uname},{url}\n"+"-"*50 +"\n"+str(e).strip()+"\n"+"-"*50 + "\n")
        #     need_new_browser = True
        #     b.quit()
        #     error += 1
        #     if error > max_error:
        #         sys.exit()
            


do_debug = 0
main()
