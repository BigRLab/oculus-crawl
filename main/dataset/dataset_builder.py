#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
from multiprocessing import Lock
from shutil import make_archive, move, rmtree

import time

from main.dataset.generic_dataset import GenericDataset
from main.service.service import Service
from main.service.status import SERVICE_CRAWLING_DATA, SERVICE_FETCHING_DATA, SERVICE_COMPRESSING_DATA, \
    SERVICE_PUBLISHING_DATA, SERVICE_CREATED_DATASET, SERVICE_FILTERING_DATA

__author__ = "Ivan de Paz Centeno"

DEFAULT_DATASET_DIR = "/tmp/"
DEFAULT_WAIT_TIME_SECONDS = 5  # time before starting to fetch data


class DatasetBuilder(Service):
    """
    Wraps a session to build a dataset with the specified name.
    The dataset builder will download all the crawled content for the given session (remote or not) and
    then build a .zip file that after that is published in a route (which can be a web server homedir).

    It is a service, meaning that it can be started in background. The progress of the build process can be retrieved
    with the get_percent_done() method. A 100 percent indicates that the dataset is successfully built, but it may not
    be packaged or published yet. In order to ensure that the process has finished, check the status of the service
    in order to match SERVICE_CREATED_DATASET.

    This service does not need to be stopped manually since it ends the background process whenever it finishes, unless
    the process must be finished beforehand.
    """
    def __init__(self, search_session, name, autostart=True, dataset_type=GenericDataset,
                 default_dataset_dir="/tmp/", publish_dir="/var/www/html/", autoclose_search_session_on_exit=False,
                 on_finished=None):
        Service.__init__(self)
        self.search_session = search_session

        self.dataset = dataset_type(name, self.search_session, "{}".format(os.path.join(default_dataset_dir, name)))

        self.percent_crawled = 0
        self.percent_fetched = 0
        self.lock = Lock()
        self.autoclose_search_session_on_exit = autoclose_search_session_on_exit
        self.on_finished = on_finished
        self.name = name
        self.publish_dir = publish_dir

        if autostart:
            self.start()

    def get_dataset_name(self):
        return self.name

    def get_search_session(self):
        return self.search_session

    def __internal_thread__(self):
        Service.__internal_thread__(self)

        # 1. We wait for the async crawlers to finish the session
        percent_crawled = 0
        percent_fetched = 0
        previous_status = self.get_status()
        start_time = time.time()

        while not self.__get_stop_flag__() and self.search_session.size() == 0 and self.search_session.get_completion_progress() == 0:
            time.sleep(1)

        #print("Stop flag: {}".format(self.__get_stop_flag__()))

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

            time.sleep(0.05)

        if not self.__get_stop_flag__():
            self.dataset.build_metadata()
            self.search_session.save_session(os.path.join(self.dataset.get_root_folder(), "search_session.ses"))

            self.__set_status__(SERVICE_FILTERING_DATA)
            # TODO: Invoke a filter for the data at this stage (if wanted)
            # It may be a good idea because it hasn't been packaged yet, however it may increase the load
            # of the machine.
            # The dataset content's are stored in self.dataset
            # The dataset folder is self.dataset.get_root_folder()
            # The metadata ground truth is located in self.dataset.get_metadata_file()

            self.__set_status__(SERVICE_COMPRESSING_DATA)
            self._make_archive()
            filename = "{}.zip".format(self.dataset.get_name())

            self.__set_status__(SERVICE_PUBLISHING_DATA)
            move("./{}".format(filename), os.path.join(self.publish_dir, filename))

            rmtree(self.dataset.get_root_folder())
            self.__set_status__(SERVICE_CREATED_DATASET)

        del self.dataset

        if self.autoclose_search_session_on_exit:
            self.search_session.stop()

        if self.on_finished:
            self.on_finished(self.get_dataset_name())

    def get_percent_done(self):
        with self.lock:
            percent_crawled = self.percent_crawled
            percent_fetched = self.percent_fetched

        return percent_crawled, percent_fetched

    def _make_archive(self):
        make_archive(self.dataset.get_name(), 'zip', self.dataset.get_root_folder(), verbose=1)
