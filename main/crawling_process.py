#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import logging
import random
from time import sleep, time
from main.crawler_service import CrawlerService
from main.dataset.remote_dataset_factory import RemoteDatasetFactory
from main.service.global_status import global_status
from main.service.service import Service

__author__ = 'Iván de Paz Centeno'


class CrawlingProcess(Service):

    def __init__(self, remote_url, crawler_processes=1, wait_time_between_tries=1):
        """
        Initializes the crawling process for the specified URL.
        :param remote_url: URL of a dataset factory.
        :param crawler_processes:
        :param wait_time_between_tries:
        :return:
        """
        Service.__init__(self)
        self.remote_url = remote_url
        self.crawler_processes = crawler_processes
        self.wait_time_between_tries = wait_time_between_tries

        self.crawler_service = None
        self.remote_dataset_factory = RemoteDatasetFactory(remote_url)

    def _find_session(self):
        """
        Retrieves a valid session from the list.
        :return:
        """
        global_status.update_proc("Accessing remote dataset factory at {}".format(self.remote_url))

        try:
            datasets_names = self.remote_dataset_factory.get_dataset_builder_names()
        except Exception as ex:
            raise Exception("Remote dataset factory is not active at {}".format(self.remote_url))

        # We pick a random session from the list
        selected_session = None

        while len(datasets_names) > 0 and selected_session is None and not self.__get_stop_flag__():
            name = random.choice(list(datasets_names))
            random_session = self.remote_dataset_factory.get_session_from_dataset_name(name)
            datasets_names.remove(name)

            if random_session.get_completion_progress() < 100:
                selected_session = random_session

            if len(datasets_names) == 0 and not selected_session:
                raise Exception("No datasets' sessions available")

            logging.info("Selected session ({}) from dataset \"{}\" to crawl".format(selected_session.backend_url, name))
            global_status.update_proc("Selected session \"{}\"".format(selected_session.backend_url))

        return selected_session

    def _feed_crawler(self, selected_session):
        """
        Feeds the crawler with the specified session.
        :param session:
        :return:
        """

        if self.crawler_service is None:

            self.crawler_service = CrawlerService(selected_session, processes=self.crawler_processes)
            self.crawler_service.start()

        else:
            self.crawler_service.update_search_session(search_session=selected_session)

        global_status.update_proc("Waiting for session \"{}\"".format(selected_session.backend_url))
        global_status.update_proc_progress("Retrieving data from search engines...",
                                    selected_session.get_completion_progress())

        while selected_session.get_completion_progress() != 100 and not self.__get_stop_flag__():
            seconds_frozen = 0
            ping_done = time()
            self.crawler_service.do_ping(ping_done)

            while self.crawler_service.get_pong() != ping_done and not self.__get_stop_flag__():
                sleep(1)
                seconds_frozen += 1

                if seconds_frozen > 60:
                    print("Crawler seems completely frozen!!!")

            sleep(1)

        #selected_session.wait_for_finish()

        logging.info("Finished crawling session ({}) from "
                     "dataset \"{}\" to crawl".format(selected_session.backend_url, name))

    def stop(self, wait_for_finish=True):
        Service.stop(self, wait_for_finish=wait_for_finish)

        if self.crawler_service:
            self.crawler_service.stop(wait_for_finish=wait_for_finish)

    def __internal_thread__(self):
        """
        Background thread to be executed.
        :return:
        """
        while not self.__get_stop_flag__():
            try:
                session = self._find_session()
                self._feed_crawler(session)

            except Exception as ex:
                global_status.update_proc("Nothing to crawl: {}".format(ex))
                logging.info("Nothing to crawl: {}".format(ex))
                logging.info("Waiting {} seconds before querying again".format(self.wait_time_between_tries))
                sleep(self.wait_time_between_tries)
