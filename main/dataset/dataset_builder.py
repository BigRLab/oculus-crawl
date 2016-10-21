#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
from multiprocessing import Lock
from shutil import make_archive, move, rmtree

import time

from main.dataset.generic_dataset import GenericDataset
from main.service.service import Service

__author__ = "Ivan de Paz Centeno"

DEFAULT_DATASET_DIR = "/tmp/"
PUBLISH_DIR = "/var/www/datasets/"

# Check service.py to know the reason for the number constants.
SERVICE_CRAWLING_DATA = -1
SERVICE_FETCHING_DATA = -2
SERVICE_COMPRESSING_DATA = -3
SERVICE_PUBLISHING_DATA = -4
SERVICE_CREATED_DATASET = 2

DEFAULT_WAIT_TIME_SECONDS = 5  # time before starting to fetch data

def get_status_name(status_code):
    result = "UNKNOWN"

    if status_code == SERVICE_CRAWLING_DATA:
        result = "SERVICE_CRAWLING_DATA"
    elif status_code == SERVICE_FETCHING_DATA:
        result = "SERVICE_FETCHING_DATA"
    elif status_code == SERVICE_COMPRESSING_DATA:
        result = "SERVICE_COMPRESSING_DATA"
    elif status_code == SERVICE_PUBLISHING_DATA:
        result = "SERVICE_PUBLISHING_DATA"
    elif status_code == SERVICE_CREATED_DATASET:
        result = "SERVICE_CREATED_DATASET"

    return result


class DatasetBuilder(Service):

    def __init__(self, search_session, name, autostart=True, dataset_type=GenericDataset):
        Service.__init__(self)
        self.search_session = search_session
        self.dataset = dataset_type(name, self.search_session, "{}".format(os.path.join(DEFAULT_DATASET_DIR, name)))

        self.percent_crawled = 0
        self.percent_fetched = 0
        self.lock = Lock()

        if autostart:
            self.start()

    def __internal_thread__(self):
        Service.__internal_thread__(self)

        # 1. We wait for the async crawlers to finish the session
        percent_crawled = 0
        percent_fetched = 0
        previous_status = self.get_status()
        start_time = time.time()

        while not self.__get_stop_flag__() and (percent_crawled < 100 or percent_fetched < 100):

            if percent_crawled < 100 or time.time() - start_time < DEFAULT_WAIT_TIME_SECONDS:
                if previous_status != SERVICE_CRAWLING_DATA:
                    self.__set_status__(SERVICE_CRAWLING_DATA)
                    previous_status = SERVICE_CRAWLING_DATA

                percent_crawled = self.search_session.get_completion_progress()

            else:
                if previous_status != SERVICE_FETCHING_DATA:
                    self.__set_status__(SERVICE_FETCHING_DATA)
                    previous_status = SERVICE_FETCHING_DATA

                    self.dataset.fetch_data(False)

                percent_fetched = self.dataset.get_percent_fetched()

            with self.lock:
                self.percent_crawled = percent_crawled
                self.percent_fetched = percent_fetched

        self.dataset.build_metadata()
        self.search_session.save_session(os.path.join(self.dataset.get_root_folder(), "search_session.ses"))

        self.__set_status__(SERVICE_COMPRESSING_DATA)
        self._make_archive()
        filename = "{}.zip".format(self.dataset.get_name())

        move("./{}".format(filename), os.path.join(PUBLISH_DIR, filename))
        rmtree(self.dataset.get_root_folder())
        self.__set_status__(SERVICE_CREATED_DATASET)

        del self.dataset

    def get_percent_done(self):
        return self.percent_crawled, self.percent_fetched

    def _make_archive(self):
        make_archive(self.dataset.get_name(), 'zip', self.dataset.get_root_folder(), verbose=1)