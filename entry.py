#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
from time import sleep

from main.crawler_service import CrawlerService
from main.dataset.data_fetcher import DataFetcher
from main.dataset.dataset_builder import DatasetBuilder, SERVICE_CREATED_DATASET, get_status_name
from main.dataset.dataset_factory import DatasetFactory
from main.dataset.generic_dataset import GenericDataset
from main.dataset.remote_dataset_factory import RemoteDatasetFactory
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


dataset_factory = DatasetFactory()
remote_dataset_factory = RemoteDatasetFactory("localhost")


def test_dataset_factory(message_prefix, dataset_factory):

    try:
        print(message_prefix, dataset_factory.get_dataset_builder_names())
        print(message_prefix, dataset_factory.create_dataset("probando"))
        print(message_prefix, dataset_factory.get_dataset_builder_names())
        print(message_prefix, dataset_factory.get_dataset_builder_percent("probando"))
        print(message_prefix, dataset_factory.get_session_from_dataset_name("probando"))
        print(message_prefix, dataset_factory.get_dataset_builders_sessions())
        print(message_prefix, dataset_factory.remove_dataset_builder_by_name("probando"))
    except Exception as ex:
        print(ex)

test_dataset_factory("remote", remote_dataset_factory)
test_dataset_factory("local", dataset_factory)


dataset_factory.stop()

'''
search_session = SearchSession()
#search_session_remote = RemoteSearchSession("localhost")
#search_session_remote.load_session("/tmp/local-search-session.jsn")

started = False

if os.path.exists("/home/ivan/session_now.ses"):
    search_session.load_session("/home/ivan/session_now.ses")
else:
    search_session.append_search_requests([
            SearchRequest("1 year old girl", {'face': True}, search_engine_proto=HowOldImages),
            #SearchRequest("1 year old girl", {'face': True}, search_engine_proto=GoogleImages),
            #SearchRequest("1 year old girl", {'face': True}, search_engine_proto=YahooImages),
            #SearchRequest("1 year old girl", {'face': True}, search_engine_proto=FlickrImages),
            #SearchRequest("1 year old girl", {'face': True}, search_engine_proto=BingImages),
    ])


crawler = CrawlerService(search_session, processes=5)
crawler.start()

dataset_builder = DatasetBuilder(search_session, "TEST")

print("\n")

while dataset_builder.get_status() != SERVICE_CREATED_DATASET:
    crawled, fetched = dataset_builder.get_percent_done()
    print("\rSTATUS: {}; CRAWLED: {}%; FETCHED: {}%".format(
        get_status_name(dataset_builder.get_status()),
        crawled, fetched
    ), end='')
    sleep(1)

print("\rSTATUS: {}; CRAWLED: {}%; FETCHED: {}%\n".format(
    get_status_name(dataset_builder.get_status()),
    100, 100
))

dataset_builder.stop()
crawler.stop()
search_session.stop()
'''