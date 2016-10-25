#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging

import sys

from main.dataset.remote_dataset_factory import RemoteDatasetFactory
from main.search_engine.google_images import GoogleImages
from main.search_session.search_request import SearchRequest

__author__ = "Ivan de Paz Centeno"



root = logging.getLogger()
root.setLevel(logging.INFO)
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
root.addHandler(ch)

remote_dataset_factory = RemoteDatasetFactory("localhost")

# We want now to inject some search.

remote_dataset_factory.create_dataset("test2")
remote_session = remote_dataset_factory.get_session_from_dataset_name("test2")

remote_session.append_search_requests([SearchRequest("1 yo boy", {'face':True}, GoogleImages)])

