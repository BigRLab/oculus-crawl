#!/usr/bin/env python
# -*- coding: utf-8 -*-

from main.service.request_pool import RequestPool
from main.service.service import Service
from main.service.socket_interface import SocketInterface
from time import sleep

import logging

__author__ = "Ivan de Paz Centeno"


# Number of elements that the service is going to keep at least in the queue, at all the time.
QUEUE_MIN_BUFFER = 50

class CrawlerService(Service, SocketInterface, RequestPool):

    def __init__(self, search_session, time_secs_between_requests=0.5, processes=1,
                 host="127.0.0.1", port=8370):
        logging.info("Initializing Crawler Service on host {}:{} for {} processes and {} secs between requests.".format(
            host, port, processes, time_secs_between_requests
        ))

        Service.__init__(self)
        SocketInterface.__init__(self, host=host, port=port)
        RequestPool.__init__(self, processes, time_secs_between_requests)

        self.time_secs_between_requests = time_secs_between_requests
        self.processes = processes
        self.search_session = search_session

        assert self.search_session
        logging.info("Crawler Service initialized. Listening and waiting for requests.")

    def process_finished(self, wrapped_result):
        search_request = wrapped_result[0]
        crawl_result = wrapped_result[1]

        # Log to session
        self.search_session.add_entry(search_request)

        logging.info("[{}%] Results for request {} retrieved: {}.".format(
            self.search_session.get_completion_progress(), search_request, len(crawl_result)
        ))

        if self.search_session.get_completion_progress() == 100:
            logging.info("Crawler finished.")

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

        while not self.__get_stop_flag__():

            with self.lock:
                if self.processing_queue.qsize() < QUEUE_MIN_BUFFER:
                    search_request = self.search_session.pop_new_search_request()

                    if search_request:
                        self.queue_request(search_request)
                    else:
                        sleep(0.1)

                else:
                    sleep(0.1)