#!/usr/bin/env python
# -*- coding: utf-8 -*-
from time import sleep

from main.dataset.data_holder.mem_database import MemDatabase
from main.service.fetch_pool import FetchPool
from main.service.service import Service, SERVICE_STOPPED

__author__ = "Ivan de Paz Centeno"

QUEUE_MIN_BUFFER = 100


class DataFetcher(FetchPool, Service):
    def __init__(self, to_folder):
        FetchPool.__init__(self)
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
        [self.database.append(request['url'], request) for request in request_list]

    def process_finished(self, wrapped_result):
        self.database.add_result_data(wrapped_result[0], wrapped_result[1])