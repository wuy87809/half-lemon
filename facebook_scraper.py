import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime, timedelta
import json
import csv
import time
import os
from dotenv import load_dotenv

class FacebookScraper:
    def __init__(self):
        load_dotenv()
        self.driver = None
        self.base_url = "https://www.facebook.com"
        self.search_keyword = "馬英九"
        self.posts = []

    def setup_driver(self):
        """设置Selenium WebDriver"""
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')  # 无头模式
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        self.driver = webdriver.Chrome(options=options)

    def login(self):
        """使用环境变量中的账号密码登录Facebook"""
        email = os.getenv('FB_EMAIL')
        password = os.getenv('FB_PASSWORD')
        
        self.driver.get(f"{self.base_url}/login")
        try:
            email_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, "email"))
            )
            password_field = self.driver.find_element(By.NAME, "pass")
            
            email_field.send_keys(email)
            password_field.send_keys(password)
            password_field.submit()
            
            time.sleep(5)  # 等待登录完成
        except Exception as e:
            print(f"登录失败: {str(e)}")
            return False
        return True

    def search_posts(self):
        """搜索过去12小时内的贴文"""
        search_url = f"{self.base_url}/search/posts/?q={self.search_keyword}"
        self.driver.get(search_url)
        time.sleep(5)  # 等待页面加载

        # 设置时间过滤（过去12小时）
        twelve_hours_ago = datetime.now() - timedelta(hours=12)

        # 滚动页面以加载更多内容
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        while True:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

        # 查找所有贴文
        posts = self.driver.find_elements(By.CSS_SELECTOR, '[role="article"]')
        
        for post in posts:
            try:
                # 提取贴文信息
                post_data = {
                    'content': post.find_element(By.CSS_SELECTOR, '[data-ad-comet-preview="message"]').text,
                    'timestamp': post.find_element(By.CSS_SELECTOR, 'a[role="link"] span').text,
                    'author': post.find_element(By.CSS_SELECTOR, 'strong').text,
                    'link': post.find_element(By.CSS_SELECTOR, 'a[role="link"]').get_attribute('href')
                }
                self.posts.append(post_data)
            except Exception as e:
                print(f"提取贴文信息时出错: {str(e)}")
                continue

    def save_to_json(self, filename='fb_posts.json'):
        """保存结果为JSON格式"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.posts, f, ensure_ascii=False, indent=2)

    def save_to_csv(self, filename='fb_posts.csv'):
        """保存结果为CSV格式"""
        if not self.posts:
            return
        
        with open(filename, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=self.posts[0].keys())
            writer.writeheader()
            writer.writerows(self.posts)

    def run(self):
        """运行爬虫"""
        try:
            self.setup_driver()
            if self.login():
                self.search_posts()
                self.save_to_json()
                self.save_to_csv()
                print(f"成功抓取 {len(self.posts)} 条贴文")
            else:
                print("登录失败，无法继续")
        finally:
            if self.driver:
                self.driver.quit()

if __name__ == "__main__":
    scraper = FacebookScraper()
    scraper.run()