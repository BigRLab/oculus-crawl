#!/usr/bin/env python
# -*- coding: utf-8 -*-
from time import sleep

from main.dataset.data_holder.mem_database import MemDatabase
from main.service.fetch_pool import FetchPool
from main.service.service import Service, SERVICE_STOPPED

__author__ = "Ivan de Paz Centeno"

QUEUE_MIN_BUFFER = 100


class DataFetcher(FetchPool, Service):
    """
    Service for fetching URLs data distributed among a pool of processes.
    """

    def __init__(self, to_folder):
        FetchPool.__init__(self, pool_limit=20)
        Service.__init__(self)
        self.database = MemDatabase(to_folder)

    def __internal_thread__(self):
        Service.__internal_thread__(self)
        do_sleep = 0

        while not self.__get_stop_flag__():

            with self.lock:
                if self.processing_queue.qsize() < QUEUE_MIN_BUFFER:
                    download_request = self.database.pop_url()

                    if download_request:
                        self.queue_download(download_request)
                    else:
                        do_sleep = 0.1

                else:
                    do_sleep = 0.1

            if do_sleep:
                sleep(do_sleep)
                do_sleep = 0

        self.__set_status__(SERVICE_STOPPED)

    def fetch_requests(self, request_list):
        """
        Fetchs the data url associated with the request.

        :param request_list: a list of JSON-formatted results retrieved from the search_session-crawled requests.
        :return:
        """
        request_list = self._discard_invalid_requests(request_list)
        [self.database.append(request['url'], request) for request in request_list]

    @staticmethod
    def _discard_invalid_requests(request_list):
        new_request_list = []

        for request in request_list:
            if 'url' in request and 'width' in request and 'height' in request and 'desc' in request and 'source' in request:
                new_request_list.append(request)

        discarded_requests = len(request_list) - len(new_request_list)

        print ("Discarded {} requests for being invalid.".format(discarded_requests))
        return new_request_list

    def process_finished(self, wrapped_result):
        self.database.add_result_data(wrapped_result[0], wrapped_result[1], wrapped_result[2])

    def get_percent_done(self):
        return self.database.get_percent_done()

    def get_results(self):
        """
        Retrieves the results from the database, in JSON format that can be used to build a metadata for the dataset.
        :return:
        """
        return self.database.get_result_data()
