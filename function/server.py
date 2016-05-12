#!/usr/bin/env python
# coding:utf-8
# manning  2015-1-27
'''
            2015.3.28
            增加了获取form内容的部分
            0，获取form表单
            1，随机http header
            2，获取的内容丢入mysql
            3，非重复性丢进数据库

            2015.3.28
            抓取模型
            0，广度优先（缺省）
            1，深度优先
            2，随机优先

            2015.3.27
            加入数据队列，单起一个线程写入数据库
            数据库类型为sqlite
            预计支持mysql、sql server等

            2015。3.26
            添加深度控制

            2015.3.8
            server退出机制
            1，超过爬取时间
            2，爬取线程不存在(可能爬完)
            3，深度超越
            4，抓取个数超越

            2016.1.22
            针对form进行筛选，提取form表单中的action以及对于的name值
            1.部分改用requess库，支持比较好
            2.针对请求超过60秒的作丢弃处理

            线程退出机制
            如果此线程5分钟内没有工作，线程退出
'''
import urlparse
import threading
import requests
import MySQLdb
import base64
import Queue
import json
import time
import sys
import re
sys.path.append("..")

from fetch import fetcher
from crawl import crawler
from urlfilter import url_filter_no_similarity,url_filter_similarity,url_repeat_control
from dbengine import engine_db
from node import UrlNode,HtmlNode
from mysql_db_connect import MySQL
from get_form import getform
from config.config import *
'''
thread模型
'''
NOW_TIME = time.time()
QUEUE_URLNODE = Queue.Queue()
QUEUE_HTMLNODE = Queue.Queue()
QUEUE_SMART_NODE = Queue.Queue()
QUEUE_COMPLETE_NODE = Queue.Queue()

TOTAL_COUNT = 0
REFUSE_COUNT = 0
EXIT_FLAG = 0

def timestamp():
    return str(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))

def single_thread(mytuple,QUEUE_HTMLNODE,DOWNLOAD_MODE,start_urls):
    #打印信息:
    #时间  结点深度  html的长度  URL队列长度  下载的数量  过滤掉的数量  相似结点队列长度  非重结点队列长度  当前爬取的URL
    global TOTAL_COUNT
    global EXIT_FLAG
    global QUEUE_URLNODE
    stop_flag = 0
    while stop_flag < 15:
        if mytuple[0].qsize() > 0:
            stop_flag = 0
            node = mytuple[0].get()
            html = fetcher(node.url,DOWNLOAD_MODE)
            html_node = HtmlNode(node.url,html,timestamp(),node.depth)
            QUEUE_HTMLNODE.put(html_node)
            TOTAL_COUNT += 1
            if len(html) > 0:
                #print timestamp()+'\t'+str(node.depth)+'\t'+str(len(html))+'\t'+str(QUEUE_URLNODE.qsize())+'\t'+str(TOTAL_COUNT)+'\t'+str(REFUSE_COUNT) + '\t' +str(QUEUE_SMART_NODE.qsize()) + '\t' + str(QUEUE_COMPLETE_NODE.qsize()) + '\t' + node.url
                print str(node.depth)+'\t'+str(QUEUE_SMART_NODE.qsize()) + '\t' + node.url
                result = getform(node.url)

                dbconfig = {'host': '127.0.0.1','user': 'root','passwd': 'mysqlroot','port': 3307,'db':'w3a_scan','charset': 'utf8'}
                db = MySQL(dbconfig)
                '''
                SET NAMES utf8;
                SET FOREIGN_KEY_CHECKS = 0;

                -- ----------------------------
                --  Table structure for `spider_result`
                -- ----------------------------
                DROP TABLE IF EXISTS `spider_result`;
                CREATE TABLE `spider_result` (
                  `id` int(11) NOT NULL AUTO_INCREMENT,
                  `start_url` varchar(200) NOT NULL,
                  `url` varchar(500) NOT NULL,
                  `newurl` varchar(500) NOT NULL,
                  `data` varchar(4000) NOT NULL,
                  `time` varchar(200) NOT NULL,
                  PRIMARY KEY (`id`)
                ) ENGINE=MyISAM DEFAULT CHARSET=utf8;
                SET FOREIGN_KEY_CHECKS = 1;
                '''
                if result is not None:
                    for lists in result:
                        data = base64.b64encode(json.dumps(lists["probe"]))
                        newurl = lists["probe"]['url']
                        #print lists["probe"]["payload"]
                        #print type(lists["probe"]["payload"])
                        sqlSearch = "select data from spider_result where newurl= '%s' and start_url = '%s'" % (newurl,start_urls[0])
                        #print "查询语句"+sqlSearch
                        #print "查询结果是"+str(db.query(sql=sqlSearch))
                        if int(db.query(sql=sqlSearch)) > 0:
                            #print "重复条件满足"
                            result = db.fetchAllRows()
                            for row in result:
                                result = json.loads(base64.b64decode(row[0]))
                                cmps = cmp(lists["probe"]["payload"].encode("utf-8"),result["payload"])
                                if int(cmps) == 0:
                                    #print "重复了"
                                    continue
                                else:
                                    #print "已有记录，但是payload不一致，重新插入"
                                    sqlInsert = "insert into spider_result(id,start_url,url,newurl,data,time) values ('','%s','%s','%s','%s','%s')" % (start_urls[0],node.url,newurl,data,timestamp())
                                    print db.insert(sql=sqlInsert), 'from'+'\t'+ str(node.url)+'\t'+'insert'+'\t'+str(newurl)+'\t'+str(timestamp())
                                    continue
                        #不曾查询到，全新直接插入
                        else:
                            sqlInsert = "insert into spider_result(id,start_url,url,newurl,data,time) values ('','%s','%s','%s','%s','%s')" % (start_urls[0],node.url,newurl,data,timestamp())
                            #print sqlInsert
                            print db.insert(sql=sqlInsert),'from'+'\t'+ str(node.url)+'\t'+'insert'+'\t'+str(newurl)+'\t'+str(timestamp())
                #    pass
                #else:
                #    print data

        else:
            stop_flag += 1
            time.sleep(5)
    EXIT_FLAG += 1



def init_urlnode(start_urls_list):
    nodelist = []
    for i in start_urls_list:
        tmpnode = UrlNode(i,'','',timestamp(),'',-1)
        nodelist.append(tmpnode)
    return nodelist

def server_exit_conditions(fetch_time,thread_num,fetch_count):
    #调度退出机制函数
    if time.time() - NOW_TIME < fetch_time and EXIT_FLAG < thread_num and TOTAL_COUNT < fetch_count:
        return True
    else:
        return False

def fetch_mode(urlnode_queue,mode):
    #抓取模型函数
    templist = []
    tempqueue = Queue.Queue()
    if urlnode_queue.qsize() > 0:
        while True:
            tempnode = urlnode_queue.get()
            templist.append(tempnode)
            if urlnode_queue.qsize() == 0:
                break
        if int(mode) == 0:
            templist.sort(key=lambda node:node.depth)
            for i in templist:
                tempqueue.put(i)
            return tempqueue

        elif int(mode) == 1:
            templist.sort(key=lambda node:node.depth,reverse=True)
            for i in templist:
                tempqueue.put(i)
            return tempqueue

        elif int(mode) == 2:
            import random
            random.shuffle(templist)
            for i in templist:
                tempqueue.put(i)
            return tempqueue

        else:
            return urlnode_queue
    else:
        return urlnode_queue


def storage_queue_conditions(storage_model,node):
    #储存条件控制函数
    if storage_model == 0:
        QUEUE_COMPLETE_NODE.put(node)
    elif storage_model == 1:
        QUEUE_SMART_NODE.put(node)
    elif storage_model == 2:
        QUEUE_COMPLETE_NODE.put(node)
        QUEUE_SMART_NODE.put(node)
    else:
        pass


def server(THREAD_NUM,START_URLS,FETCH_TIME,KEY_WORD,IGNORE_KEY_WORD,DOWNLOAD_MODE,DEPTH,FETCH_COUNT,FETCH_MODE,STORAGE_MODEL,SIMILARITY,FOCUSKEYWORD):

    global REFUSE_COUNT
    global QUEUE_URLNODE
    global QUEUE_HTMLNODE

    #初始化url结点队列
    start_urls = START_URLS
    start_nodes = init_urlnode(start_urls)
    for i in start_nodes:
        QUEUE_URLNODE.put(i)
    my_tuple_list = []
    for i in xrange(THREAD_NUM):
        my_tuple_list.append((Queue.Queue(),str(i)))

    #起抓取线程
    threads_list = []
    for i in xrange(THREAD_NUM):
        threads_list.append(threading.Thread(target = single_thread,args = (my_tuple_list[i],QUEUE_HTMLNODE,DOWNLOAD_MODE,start_urls)))
    for i in threads_list:
        i.setDaemon(True)
        i.start()

    #起存储数据库线程
    #print (KEY_WORD,QUEUE_COMPLETE_NODE,QUEUE_SMART_NODE,STORAGE_MODEL)
    db_engine = threading.Thread(target = engine_db,args = (KEY_WORD,QUEUE_COMPLETE_NODE,QUEUE_SMART_NODE,STORAGE_MODEL))
    db_engine.setDaemon(True)
    db_engine.start()

    #URL结点队列调度
    while server_exit_conditions(FETCH_TIME,THREAD_NUM,FETCH_COUNT):
        for i in my_tuple_list:
            if QUEUE_URLNODE.qsize() > 0  and i[0].qsize() < 1:
                QUEUE_URLNODE = fetch_mode(QUEUE_URLNODE,FETCH_MODE)
                node = QUEUE_URLNODE.get()
                i[0].put(node)

        if QUEUE_HTMLNODE.qsize() > 0:
            html_node = QUEUE_HTMLNODE.get()

            nodelist = crawler(html_node)

            for i in nodelist:
                if i.depth <= DEPTH and SIMILARITY == 0:#SIMILARITY
                    if url_filter_similarity(i.url,KEY_WORD,IGNORE_KEY_WORD,FOCUSKEYWORD):
                        QUEUE_URLNODE.put(i)
                        if STORAGE_MODEL == 1 or STORAGE_MODEL == 2:
                            QUEUE_SMART_NODE.put(i)
                    else:
                        REFUSE_COUNT += 1

                elif i.depth <= DEPTH and SIMILARITY == 1:
                    if url_filter_no_similarity(i.url,KEY_WORD,IGNORE_KEY_WORD,FOCUSKEYWORD):
                        QUEUE_URLNODE.put(i)
                        if STORAGE_MODEL == 0 or STORAGE_MODEL == 2:
                            QUEUE_COMPLETE_NODE.put(i)
                    else:
                        REFUSE_COUNT += 1
                else:
                    REFUSE_COUNT += 1


if __name__ == '__main__':
    server()
