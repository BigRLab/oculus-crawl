#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
from time import sleep, time
import sys


from main.crawler_service import CrawlerService
from main.dataset.remote_dataset_factory import RemoteDatasetFactory
from main.search_engine import yahoo_images, bing_images, flickr_images, google_images, howold_images
import random

from main.service.status import status

__author__ = "Ivan de Paz Centeno"

URL = "http://localhost:24005"
#root = logging.getLogger()
#root.setLevel(logging.INFO)
#ch = logging.StreamHandler(sys.stdout)
#ch.setLevel(logging.INFO)
#formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
#ch.setFormatter(formatter)
#root.addHandler(ch)

FINISH = False
CRAWLER_PROCESSES = 4
WAIT_TIME_BETWEEN_TRIES = 1    # seconds

remote_dataset_factory = RemoteDatasetFactory(URL)

# we check for new sessions to crawl
crawler = None


def print_status():
    status_string = str(status)
    status_string = "{}{}".format("\033[F" * (len(status_string.split("\n"))), status_string)
    print(status_string)

print("\n"*(CRAWLER_PROCESSES+3))
while not FINISH:

    status.update_proc("Accessing remote dataset factory at {}".format(URL))

    datasets_names = remote_dataset_factory.get_dataset_builder_names()

    try:
        # We pick a random session from the list
        selected_session = None

        while len(datasets_names) > 0 and not selected_session:
            name = random.choice(list(datasets_names))
            random_session = remote_dataset_factory.get_session_from_dataset_name(name)
            datasets_names.remove(name)

            if random_session.get_completion_progress() < 100:
                selected_session = random_session

        if len(datasets_names) == 0 and not selected_session:
            raise Exception("No datasets' sessions available")

        logging.info("Selected session ({}) from dataset \"{}\" to crawl".format(selected_session.backend_url, name))
        status.update_proc("Selected session \"{}\"".format(selected_session.backend_url))
        #print("Selected session ({}) from dataset \"{}\" to crawl".format(selected_session.backend_url, name))

        if crawler is None:

            crawler = CrawlerService(selected_session, processes=CRAWLER_PROCESSES)
            crawler.start()

        else:
            crawler.update_search_session(search_session=selected_session)

        status.update_proc("Waiting for session \"{}\"".format(selected_session.backend_url))
        status.update_proc_progress("Retrieving data from search engines...",
                                    selected_session.get_completion_progress())

        while selected_session.get_completion_progress() != 100:
            seconds_frozen = 0
            ping_done = time()
            crawler.do_ping(ping_done)

            while crawler.get_pong() != ping_done:
                sleep(1)
                seconds_frozen += 1

                if seconds_frozen > 60:
                    print("Crawler seems completely frozen!!!")

            print_status()
            sleep(1)

        #selected_session.wait_for_finish()

        logging.info("Finished crawling session ({}) from "
                     "dataset \"{}\" to crawl".format(selected_session.backend_url, name))

    except Exception as ex:
        logging.info("Nothing to crawl: {}".format(ex))
        logging.info("Waiting {} seconds before querying again".format(WAIT_TIME_BETWEEN_TRIES))
        sleep(WAIT_TIME_BETWEEN_TRIES)

status.update_proc("Finished.")
crawler.stop()
