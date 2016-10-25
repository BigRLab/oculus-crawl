#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
from time import sleep

import sys

from main.crawler_service import CrawlerService
from main.dataset.remote_dataset_factory import RemoteDatasetFactory
import random

__author__ = "Ivan de Paz Centeno"


root = logging.getLogger()
root.setLevel(logging.INFO)
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
root.addHandler(ch)

FINISH = False
CRAWLER_PROCESSES = 10
WAIT_TIME_BETWEEN_TRIES = 10    # seconds

remote_dataset_factory = RemoteDatasetFactory("localhost")


# we check for new sessions to crawl
while not FINISH:
    sessions = remote_dataset_factory.get_dataset_builders_sessions()

    try:
        # We pick a random session from the list
        selected_session = None

        while len(sessions) > 0 and not selected_session:
            name = random.choice(list(sessions))
            random_session = sessions[name]
            del sessions[name]

            if random_session.get_completion_progress() < 100:
                selected_session = random_session

        if len(sessions) == 0 and not selected_session:
            raise Exception("No datasets' sessions available")

        logging.info("Selected session ({}:{}) from dataset \"{}\" to crawl".format(selected_session.get_host(),
                                                                                    selected_session.get_port(), name))

        crawler = CrawlerService(selected_session, processes=CRAWLER_PROCESSES)
        crawler.start()

        selected_session.wait_for_finish()

        crawler.stop()
        logging.info("Finished crawling session session ({}:{}) from "
                     "dataset \"{}\" to crawl".format(selected_session.get_host(), selected_session.get_port(), name))

    except Exception as ex:
        logging.info("Nothing to crawl: {}".format(ex))
        logging.info("Waiting {} seconds before querying again".format(WAIT_TIME_BETWEEN_TRIES))
        sleep(WAIT_TIME_BETWEEN_TRIES)