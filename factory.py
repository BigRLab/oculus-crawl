#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging

import sys

from main.search_engine import yahoo_images, bing_images, google_images, howold_images, flickr_images
from main.dataset.dataset_factory import DatasetFactory
from main.search_session.search_session import SearchSession

__author__ = "Ivan de Paz Centeno"


root = logging.getLogger()
root.setLevel(logging.INFO)
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
root.addHandler(ch)

#search_session = SearchSession(port=24010)
#search_session.stop()
#search_session2 = SearchSession(port=24010)
#search_session2.stop()

########
# This line is enough for the process to work.
# The factory is now listening on port 24005.
#
dataset_factory = DatasetFactory()

logging.info("********************************")
logging.info("Listening on port {}".format(dataset_factory.get_port()))
logging.info("********************************")
