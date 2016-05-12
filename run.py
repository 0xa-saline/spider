#!/usr/bin/env python
# coding:utf-8
import os
import optparse
import time
from function.server import server
from config.config import *

def main():
    global DOWNLOAD_MODE
    global THREAD_NUM
    global KEY_WORD
    global FETCH_TIME
    global SPIDER_PROXY
    global START_URLS
    global IGNORE_KEY_WORD

    photo = """
           _______  ______   _______           _______
        (  __   )(  __  \ (  ___  )|\     /|(  ____ \
        | (  )  || (  \  )| (   ) |( \   / )| (    \/
        | | /   || |   ) || (___) | \ (_) / | (____
        | (/ /) || |   | ||  ___  |  \   /  (_____ \
        |   / | || |   ) || (   ) |   ) (         ) )
        |  (__) || (__/  )| )   ( |   | |   /\____) )
        (_______)(______/ |/     \|   \_/   \______/


                                                  by 0day5.com"""

    usage = photo
    parser = optparse.OptionParser(usage=usage)
    parser.add_option("-u", "--url",
                  dest = "url",
                  default = 'http://0cx.cc/',
                  help="Start the domain name")

    parser.add_option("-t", "--thread",
                  dest = "threads_num",
                  default = 15,
                  help="Number of threads")

    parser.add_option("--depth",
                  dest = "depth",
                  default = 1000*1000*10,
                  help="Crawling depth")

    parser.add_option("--model",
                  dest = "model",
                  default = 0,#开启混合模式
                  help='''Crawling mode: Static 0  Dynamic 1  Mixed 2''')

    parser.add_option("--policy",
                  dest = "policy",
                  default = 1,
                  help="Crawling strategy: Breadth-first 0  Depth-first 1  Random-first 2")

    parser.add_option("-k", "--keyword",
                  dest = "keyword",
                  default = '',
                  help="Focusing on the keywords in host")

    parser.add_option("--time",
                  dest = "fetch_time",
                  default = 3600*24*7,
                  help="Crawl time: The default crawl for 7 days")

    parser.add_option("--count",
                  dest = "fetch_count",
                  default = 1000*1000*10,
                  help="Crawling number: The default download 100000000 pages")

    parser.add_option("--proxy", action="store_true",
                  dest = "proxy",
                  default = False,
                  help="The proxy pattern")

    parser.add_option("--ignore",
                  dest="ignore_keyword",
                  default = '',
                  help="Filter keyword in URL's host or path")

    parser.add_option("--focus",
                  dest="focus_keyword",
                  default = '',
                  help="Focus keyword in URL's path")

    parser.add_option("--storage",
                  dest="storage_model",
                  default = 1,
                  help="Storage mode: A small model 1  Large schemas 0  Don't store  3")

    parser.add_option("--similarity",
                  dest="similarity",
                  default = 0,
                  help="Similarity check: True 0  False 1")
    '''
    parser.add_option("-s", "--zdbk", action="store_true",
                  dest="zdcl",
                  default=False,
                  help="write zdbk data to oracle db")
    '''

    (options, args) = parser.parse_args()



    download_mode = int(options.model)
    threads_num = int(options.threads_num)
    keyword = set_key_word(options.keyword)
    fetch_time = int(options.fetch_time)
    spider_proxy = options.proxy
    start_urls = set_start_urls(options.url)
    crawl_depth = int(options.depth)
    fetch_mode = int(options.policy)
    fetch_count = int(options.fetch_count)
    storage_model = int(options.storage_model)
    similarity = int(options.similarity)
    ignore_keyword = list(set(IGNORE_KEY_WORD + options.ignore_keyword.split(',')))
    focus_keyword = list(set(options.focus_keyword.split(',')))

    #print options

    #print photo
    server(threads_num,start_urls,fetch_time,keyword,ignore_keyword,download_mode,crawl_depth,fetch_count,fetch_mode,storage_model,similarity,focus_keyword)

if __name__ == "__main__":
    main()
