#!/usr/bin/env python
# -*- coding: utf-8 -*-
from main.crawler_service import CrawlerService
from main.search_engine.google_images import GoogleImages
from main.search_engine.yahoo_images import YahooImages
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

search_request = SearchRequest("asd", {'face'}, search_engine_proto=YahooImages)

search_session.append_search_requests([search_request])

search_request = SearchRequest("asd", {'face'}, search_engine_proto=GoogleImages)

search_session.append_search_requests([search_request])


crawler_service = CrawlerService(search_session, processes=2)

crawler_service.start()

signal.pause()

crawler_service.stop()