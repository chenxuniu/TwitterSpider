import time, os, sys
import selenium
import random
import datetime
import argparse
import re
import base64
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.keys import Keys
from mylib.CommonOperationClass import createCOC
from BrowserModule.BaseClass import Browser

class TweetData:
    # attribute = ["id", "date", "content", "username", "reply", "repost", "like"]
    attribute = ["id", "date", "content", "reply", "repost", "like"]


    def __setattr__(self, key, value):
        assert key in self.attribute
        self.__dict__[key] = value


    def get_content_as_line(self):
        l = ""
        for k in self.attribute:
            r = self.__getattribute__(k)
            if k == "content":
                r = base64.b64encode(r.encode("utf-8")).decode("utf-8")
            l += r +","
        l = l.rstrip(",")
        return l + "\n"


def parse_number(input_str):
    # 删除逗号
    input_str = input_str.replace(',', '')

    # 定义字母结尾对应的因子
    suffixes = {'K': 1000, 'M': 1000000, 'G': 1000000000}

    # 如果字符串以支持的字母结尾之一结尾，将其解释为相应的数量级
    for suffix, factor in suffixes.items():
        if input_str.endswith(suffix) or input_str.endswith(suffix.lower()):
            input_str = input_str[:-1]
            factor = factor
            break
    else:
        factor = 1

    try:
        # 尝试将字符串转换为浮点数
        number = float(input_str)
    except ValueError:
        print("[-]遇到新的数字表达格式:",input_str)
        return input_str

    # 乘以因子以获得最终结果
    result = number * factor
    return int(result)



def createTaskClass(COC):
    class Task(COC):
        def __init__(self, proxy = None,headless=False,use_cap=False, bit_id=None,
                     update_id=True, ads_id=None,debug_address="",version="118"):
            super(Task,self).__init__(proxy=proxy, headless=headless,
                                        bit_id=bit_id,use_cap=use_cap,update_id=update_id,ads_id=ads_id,debug_address=debug_address,version=version)
            self.login_status = False


        def w(self,wait = 5):
            time.sleep(random.uniform(wait, wait + 1))

        def check_exists_by_xpath(self,xpath,wait=5):
            try:
                t = WebDriverWait(self.driver, wait).until(
                    EC.visibility_of_element_located((By.XPATH, xpath)))
            except selenium.common.exceptions.TimeoutException:
                return False
            return True

        # 初始化存储数据的地方
        def init_store(self,url,data_dir,index_id):
            formatted_date = datetime.date.today().strftime("%Y-%m-%d")
            my_data_dir = data_dir+"_"+formatted_date
            if not os.path.exists(my_data_dir):
                os.mkdir(my_data_dir)
            # file_name = url.split("//")[1].split("/", 1)[1].replace("/", "-@-") + "." + formatted_date + ".log"
            file_name = str(index_id)+"."+url.split("//")[1].split("/")[-1] + ".log"
            self.store_path_file = my_data_dir+os.sep+file_name
            if os.path.exists(self.store_path_file):
                os.remove(self.store_path_file)
            # 初始化写入标题
            with open(self.store_path_file, "a", encoding="utf-8") as f:
                f.write(",".join(TweetData.attribute)+"\n")


        # 会在一次提取中多次调用
        def old_store(self,content):
            with open(self.store_path_file,"a",encoding="utf-8") as f:
                f.write(content + "\n" + "-"*50 + "\n")

        # 会在一次提取中多次调用
        def store(self, td):
            with open(self.store_path_file, "a", encoding="utf-8") as f:
                f.write(td.get_content_as_line())

        def cal_content_hash(self,content):
            # 使用正则表达式将所有数字替换为空
            result = re.sub(r'\d', '', content)
            return hash(result)


        def parse_content(self,article_tag,td,is_main_airticle):
            # is_comment标识是否是评论
            # author = article_tag.find_element(By.XPATH, './/div[@data-testid="User-Name"]').text
            # author = author.replace("·","").replace("\n"," ")
            # author = author.split("@")[0].strip()
            # 内容如果是转发的别人的可能有父节点为div的time节点
            time_str = ""
            # 感觉也可以取最后一个
            for time_tag in article_tag.find_elements(By.XPATH, './/time'):
                tweet_id_a = time_tag.find_element(By.XPATH, '..').get_attribute("href")
                if tweet_id_a == None:
                    continue
                tweet_id = tweet_id_a.rsplit("/",1)[1]
                time_str = time_tag.get_attribute("datetime")
                break
            # if time_str == "":
            #     print("[-]没有提取到时间，作者名字：{}".format(author))
            # time_str = article_tag.find_element(By.XPATH, './/time').get_attribute("datetime")
            # tweet_id = article_tag.find_element(By.XPATH, './/time').find_element(By.XPATH, '..').get_attribute("href").rsplit("/",1)[1] # 每个评论都有一个ID
            try:
                content = article_tag.find_element(By.XPATH, './/div[@data-testid="tweetText"]').text
            except:
                # 可能评论只有图片 tweetPhoto
                content = "[img or video]"
            try:
                if is_main_airticle:
                    group_div = article_tag.find_element(By.XPATH,'.//div[@role="group"]')
                    spans = group_div.find_elements(By.XPATH,'.//span[@data-testid="app-text-transition-container"]')
                    reply = spans[0].text
                    retweet = spans[1].text
                    like = spans[2].text
                else:
                    reply = article_tag.find_elements(By.XPATH,'.//div[@data-testid="reply"]')[0].get_attribute("aria-label")
                    reply = reply.split()[0]
                    retweet = article_tag.find_elements(By.XPATH, './/div[@data-testid="retweet"]')[0].get_attribute("aria-label")
                    retweet = retweet.split()[0]
                    like = article_tag.find_elements(By.XPATH,'.//div[@data-testid="like"]')[0].get_attribute("aria-label")
                    like = like.split()[0]
            except Exception as e:
                print(str(e))
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
            td.id = tweet_id
            td.date = time_str
            td.content = content
            # td.username = author
            td.reply = str(parse_number(reply))
            td.repost = str(parse_number(retweet))
            td.like = str(parse_number(like))
            # return "{}\n{}\n{}\n{} {} {}\n".format(author, time_str, content, reply, retweet, like)


        # 提取评论的核心逻辑
        def extract_contents(self,url,max_comments):
            print("[+]Try to get contents from {}".format(url))
            # 打开目标网页
            self.driver.get(url)
            self.w()
            extraced_content_count = 0
            # 如果向下滚动X次都没有新增内容
            max_scroll_count_without_increase = 10
            try_scroll_count = 0
            handled_div_hash = set()
            is_dicover_more = False
            is_first_reply = True
            while (try_scroll_count < max_scroll_count_without_increase) and extraced_content_count < max_comments:
                is_increase = False
                # 客户的需求是会膨胀的，必须从这个inner_div开始处理，不能直接从airticl_tag开始
                for inner_div in self.driver.find_elements(By.XPATH, '//div[@data-testid="cellInnerDiv"]'):
                    orig_content = inner_div.text # 简单粗暴的提取方法
                    if orig_content=="" or self.cal_content_hash(orig_content) in  handled_div_hash:
                        continue
                    handled_div_hash.add(self.cal_content_hash(orig_content))
                    try:
                        article_tag = inner_div.find_element(By.XPATH,".//article")
                    except NoSuchElementException:
                        pass
                    else:
                        # 发现一个很巧妙判断是否是广告的方法：
                        try:
                            article_tag.find_element(By.XPATH, './/time')
                        except:
                            continue
                        # 只提取第一个reply 可以用1590086293706641409测试
                        discover_shuxian = False
                        try:
                            inner_div.find_element(By.XPATH,
                                                   './/div[@data-testid="Tweet-User-Avatar"]/following-sibling::*[1]')
                        except NoSuchElementException:
                            if is_first_reply == False:
                                print("[-!-]发现竖线消失，本次first reply片段完毕")
                            discover_shuxian = False #没有找到那个竖线
                        else:
                            print("[-!-]发现竖线,记录本次reply")
                            discover_shuxian = True
                        # 解析真正的格式化内容
                        if is_first_reply:
                            # 这个方法太落后了
                            # for possible_text in ["Reposts", "Quotes", "Likes", "Bookmarks"]:
                            #     if possible_text in orig_content.split("\n")[-1]:
                            #         content = orig_content
                            td = TweetData()
                            if article_tag.get_attribute("tabindex") == "-1":
                                self.parse_content(article_tag,td,is_main_airticle=True)
                            else:
                                self.parse_content(article_tag,td,is_main_airticle=False)
                            self.store(td)
                            is_increase = True
                            # self.store(orig_content+"\n@@@@@@@@@@\n" + content) # 测试用的

                            extraced_content_count += 1

                        # 修改firstreply变量
                        if discover_shuxian:
                            is_first_reply = False
                        else:
                            is_first_reply = True
                    # 判断是不是结尾的Discover more，不确定这部分有没有Bug
                    try:
                        inner_div.find_element(By.XPATH, './/span[text()="Discover more"]')
                    except NoSuchElementException:
                        pass
                    else:
                        is_dicover_more = True
                        break
                    # 处理first reply以Show replies结束的情况
                    try:
                        inner_div.find_element(By.XPATH, './/span[text()="Show replies"]')
                    except NoSuchElementException:
                        pass
                    else:
                        print("[-!-]发现Show replies，本次first reply片段完毕")
                        is_first_reply = True
                    # 检查是否有Show more replies 按钮
                    try:
                        span_show_more = inner_div.find_element(By.XPATH, './/span[text()="Show more replies"]')
                    except NoSuchElementException:
                        pass
                    else:
                        print("-----发现Show more replies按钮，点击")
                        span_show_more.click()

                #————————————————————————for循环结束，进入while循环
                if is_dicover_more:
                    print("[+]-----发现Discover more，结束提取评论")
                    break
                if is_increase:
                    try_scroll_count = 0
                else:
                    try_scroll_count += 1
                # 向下滚动
                self.driver.execute_script('window.scrollBy(0,500)')
                # 显示信息
                print("-----已经提取的评论数：{} 无新增内容的向下滚动次数：{}(最大{}) 是否发现新的内容:{}".format(
                    extraced_content_count,try_scroll_count,max_scroll_count_without_increase,is_increase
                ))


                self.w()
                # self.debug_pause()
            print("[+]A total of {} contents have been obtained from {}".format(extraced_content_count, url))


        def check_login_status(self):
            self.driver.get("https://twitter.com/home")
            self.w(3)
            h2_tags = self.driver.find_elements(By.XPATH, '//h2[@role="heading"]')
            for h2 in h2_tags:
                if h2.text == "Home":
                    print("Login Success!")
                    return True
            return False


        def login(self,email,password,username):
            if self.check_login_status():
                return
            email = email.strip()
            password = password.strip()
            username = username.strip()
            # 参数末尾不能有"\n" 不然和回车效果一样
            print("[+]Try to login...")
            self.driver.get('https://twitter.com/i/flow/login')
            wait = 5
            self.w()
            email_xpath = '//input[@autocomplete="username"]'
            password_xpath = '//input[@autocomplete="current-password"]'
            username_xpath = '//input[@data-testid="ocfEnterTextTextInput"]'
            # enter email
            email_el = self.driver.find_element(By.XPATH, email_xpath)
            self.w()
            email_el.send_keys(email)
            self.w()
            email_el.send_keys(Keys.RETURN)
            self.w()
            # in case twitter spotted unusual login activity : enter your username
            if self.check_exists_by_xpath(username_xpath):
                username_el = self.driver.find_element(By.XPATH, username_xpath)
                self.w()
                username_el.send_keys(username)
                # print(username)
                # self.debug_pause()
                self.w()
                username_el.send_keys(Keys.RETURN)
                self.w()
            # enter password
            password_el = self.driver.find_element(By.XPATH, password_xpath)
            password_el.send_keys(password)
            self.w()
            password_el.send_keys(Keys.RETURN)
            self.w(wait = 6)
            print("[+]login completed")

        # 编写处理逻辑
        def run(self,url,email,password,username,max_comments,index_id):
            # if not self.login_status:
            #     self.login(email,password,username)
            #     self.login_status = True
            # if not self.check_login_status():
            #     return False
            self.init_store(url,data_dir="twitter_data",index_id=index_id)
            self.extract_contents(url,max_comments)
            return True
            # self.get_article_comment(url,max_comments)
            # self.driver.get("https://twitter.com/elonmusk/status/1685437228967686144")
            # self.w(4)
            # self.debug_pause()

    return Task

"""
hyper_link href
https://twitter.com/nOxhm/status/1594429003569438721  为啥只抓取到一个评论
"""


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Twitter spider by Saferman")
    parser.add_argument("--url", default="https://twitter.com/elonmusk/status/1685437228967686144", help="The twitter article url")
    parser.add_argument("--count", default=50,
                        help="The spidered max comments")
    args = parser.parse_args()

    b = createTaskClass(createCOC(browser=Browser))(headless=False,
                                                    proxy="socks5://127.0.0.1:10808")
    b.run(args.url, "cateyezgnppc@outlook.com","0Esilent145","MenSSGenshin",max_comments=args.count)


