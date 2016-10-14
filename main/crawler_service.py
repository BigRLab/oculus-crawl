#!/usr/bin/env python
# -*- coding: utf-8 -*-

from main.service.request_pool import RequestPool
from main.service.service import Service, SERVICE_STOPPED
from time import sleep

import logging

__author__ = "Ivan de Paz Centeno"


# Number of elements that the service is going to keep at least in the queue, all the time.
QUEUE_MIN_BUFFER = 5


class CrawlerService(Service, RequestPool):

    def __init__(self, search_session, time_secs_between_requests=0.5, processes=1):
        logging.info("Initializing Crawler Service for {} processes and {} secs between requests.".format(
            processes, time_secs_between_requests
        ))

        Service.__init__(self)
        RequestPool.__init__(self, processes, time_secs_between_requests)

        self.time_secs_between_requests = time_secs_between_requests
        self.processes = processes
        self.search_session = search_session
        self.on_process_finished = None

        assert self.search_session
        logging.info("Crawler Service initialized. Listening and waiting for requests.")

    def register_on_process_finished(self, func):
        self.on_process_finished = func

    def process_finished(self, wrapped_result):
        search_request = wrapped_result[0]
        crawl_result = wrapped_result[1]

        search_request.associate_result(crawl_result)
        # Log to session
        self.search_session.add_history_entry(search_request)

        logging.info("[{}%] Results for request {} retrieved: {}.".format(
            self.search_session.get_completion_progress(), search_request, len(crawl_result)
        ))

        if self.search_session.get_completion_progress() == 100:
            logging.info("Crawler finished.")

        if self.on_process_finished:
            self.on_process_finished(search_request, crawl_result)

    def start(self):
        logging.info("Crawler started digesting requests.")
        Service.start(self)
        self.resume()

    def resume(self):
        self.stop_processing = False
        self.process_queue()

    def pause(self):
        self.stop_processing = True

    def stop(self, wait_to_finish=True):
        logging.info("Crawler stopped from digesting requests.")
        Service.stop(self, wait_to_finish)

    def __internal_thread__(self):
        Service.__internal_thread__(self)
        do_sleep = 0

        while not self.__get_stop_flag__():

            with self.lock:
                if self.processing_queue.qsize() < QUEUE_MIN_BUFFER:
                    search_request = self.search_session.pop_new_search_request()

                    if search_request:
                        self.queue_request(search_request)
                    else:
                        do_sleep = 0.5

                else:
                    do_sleep = 0.3

            if do_sleep:
                sleep(do_sleep)
                do_sleep = 0

        self.__set_status__(SERVICE_STOPPED)
