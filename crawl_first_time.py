# -*- encoding: utf8 -*-
from bs4 import BeautifulSoup
import requests
import datetime
import time
import jieba
from apscheduler.schedulers.blocking import BlockingScheduler
from db_connect.connection import con
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import re

sched = BlockingScheduler()
db = con.cursor()
stopwords = []

with open('stop_words.txt','r', encoding='utf8') as stopword:
    for word in stopword:
        stopwords.append(word.replace("\n",""))
jieba.load_userdict('moe.dict')

def crawlnews():
    today = datetime.date.today()
    stop = False
    res = requests.get('https://udn.com/news/breaknews/1/')
    res.encoding = "utf-8"
    soup = BeautifulSoup(res.text, "html.parser")
    driver = webdriver.PhantomJS()
    driver.get('https://udn.com/news/breaknews/1/')
    db.execute("DELETE FROM news_info WHERE '" + str(today) + "'-pub_date>=10")
    con.commit()
    ch = re.compile(u'[\u3400-\u9FFF]+')
    while not stop :
        stop = True
        for item in soup.select("#breaknews_body > dl > dt") :
            title = u'{}'.format(item.select("h2 > a")[0].text)
            db.execute("SELECT * FROM news_info WHERE title=%s", (title, ))
            date = str(today.year) + "-" + item.select(".info > .dt")[0].text.split(" ")[0]
            other_day = datetime.datetime.strptime(date, '%Y-%m-%d').date()
            dif = today - other_day
            if dif.days>=10 :
                stop = True
                break
            if db.fetchone() :
                print ("existed   " + title)
            else :
                link = 'https://udn.com'+item.select("h2 > a")[0].get('href')
                content_res = requests.get(link)
                content_res.encoding = "utf-8"
                content_soup = BeautifulSoup(content_res.text, "html.parser")
                content = ""
                for sentence in content_soup.select("#story_body_content > p") :
                    content = content + sentence.text
                chlist = ch.findall(content)
                words = jieba.cut(" ".join(chlist),cut_all=False)
                words = list(words)
                content = ""
                for w in words :
                    if w not in stopwords :
                        content = content + w + " "
                db.execute("INSERT INTO news_info (title, pub_date, content, link) VALUES (%s, %s, %s, %s)",(title, date, content, link))
                stop = False
                print ("insert data  " + title)
        if not stop :        
            driver.find_element_by_id('more').click()
            time.sleep(5)
            soup = BeautifulSoup(driver.page_source,"html.parser")
            con.commit()
    driver.close()
    print ("OK")
    


crawlnews()

