#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
from time import sleep

from main.crawler_service import CrawlerService
from main.dataset.data_fetcher import DataFetcher
from main.dataset.generic_dataset import GenericDataset
from main.search_engine.bing_images import BingImages
from main.search_engine.flickr_images import FlickrImages
from main.search_engine.google_images import GoogleImages
from main.search_engine.howold_images import HowOldImages
from main.search_engine.yahoo_images import YahooImages
from main.search_session.remote_search_session import RemoteSearchSession
from main.search_session.search_request import SearchRequest
from main.search_session.search_session import SearchSession
import signal

import logging
import sys

root = logging.getLogger()
root.setLevel(logging.INFO)
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
root.addHandler(ch)


__author__ = "Ivan de Paz Centeno"

search_session = SearchSession()
#search_session_remote = RemoteSearchSession("localhost")
#search_session_remote.load_session("/tmp/local-search-session.jsn")

started = False

if os.path.exists("/home/ivan/session_now.ses"):
    search_session.load_session("/home/ivan/session_now.ses")
else:
    search_session.append_search_requests([
            #SearchRequest("1 year old girl", {'face': True}, search_engine_proto=HowOldImages),
            SearchRequest("1 year old girl", {'face': True}, search_engine_proto=GoogleImages),
            #SearchRequest("1 year old girl", {'face': True}, search_engine_proto=YahooImages),
            #SearchRequest("1 year old girl", {'face': True}, search_engine_proto=FlickrImages),
            SearchRequest("1 year old girl", {'face': True}, search_engine_proto=BingImages),
    ])

    crawler = CrawlerService(search_session, processes=5)
    crawler.start()
    search_session.wait_for_finish()
    search_session.save_session("/home/ivan/session_now.ses")
    started = True

dataset = GenericDataset("generic_image", search_session, '/home/ivan/test_dataset/')

dataset.fetch_data()
dataset.build_metadata()
print("************************************************")
print("************************************************")
print("************************************************")
print("************************************************")
print("************************************************")

logging.info("Finishing dataset.")
del dataset
logging.info("Dataset finished.")
search_session.stop()
logging.info("Search_session finished.")

if started:
    crawler.stop()
print("************************************************")
print("************************************************")
print("************************************************")
print("************************************************")
print("************************************************")

"""
search_session = SearchSession()
remote_search_session = RemoteSearchSession("localhost")

#search_request = SearchRequest("asd", {'face': True}, search_engine_proto=YahooImages)
#search_session.append_search_requests([search_request])

#search_request = SearchRequest("asd2", {'face': True}, search_engine_proto=GoogleImages)
#search_session.append_search_requests([search_request])

#search_session.load_session("/tmp/remote-search-session.jsn")
remote_search_session.load_session("/tmp/local-search-session.jsn")

#search_session.stop()


crawler_service = CrawlerService(remote_search_session, processes=1)

crawler_service2 = CrawlerService(search_session, processes=1)

crawler_service.start()
crawler_service2.start()

while search_session.get_completion_progress() < 100:
    print ("Completion progress: {}%".format(search_session.get_completion_progress()), end="\r")
    sleep(1)

crawler_service.stop()
crawler_service2.stop()

print("[LOCAL] Completion progress: {}".format(search_session.get_completion_progress()))
print("[REMOTE] Completion progress: {}".format(remote_search_session.get_completion_progress()))

print("[LOCAL] Size: {}".format(search_session.size()))
print("[REMOTE] Size: {}".format(remote_search_session.size()))

print("[REMOTE] pop: {}".format(remote_search_session.pop_new_search_request()))
print("[LOCAL] Size: {}".format(remote_search_session.size()))

print("[LOCAL] pop: {}".format(search_session.pop_new_search_request()))
print("[REMOTE] Size: {}".format(remote_search_session.size()))

print(search_session.get_history())
for key in search_session.get_history():
    print("Result: {}".format(search_session.get_history()[key].get_result()))

search_session.stop()
"""
"""
#search_request = SearchRequest("asd", {'face'}, search_engine_proto=GoogleImages)

search_request = SearchRequest("1 year old girl", {'face'}, search_engine_proto=FlickrImages)

search_session.append_search_requests([search_request])



while search_session.get_completion_progress() < 100:
    print ("Completion progress: {}%".format(search_session.get_completion_progress()), end="\r")
    sleep(1)

crawler_service.stop()
"""