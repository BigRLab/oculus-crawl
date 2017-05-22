#!/usr/bin/env python
# -*- coding: utf-8 -*-

from threading import Lock
from main.service.request_pool import RequestPool
from main.service.service import Service, SERVICE_STOPPED
from time import sleep
import logging
from main.service.global_status import  global_status


__author__ = "Ivan de Paz Centeno"


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

        # Anti freeze system. Ping can be set externally, meanwhile pong is set internally.
        self.ping = 0
        self.pong = 0
        self.ping_lock = Lock()

        assert self.search_session
        logging.info("Crawler Service initialized. Listening and waiting for requests.")

    def do_ping(self, value):
        with self.ping_lock:
            self.ping = value

    def get_pong(self):
        with self.ping_lock:
            result = self.pong

        return result

    def update_search_session(self, search_session):
        """
        Updates the search session of the current crawler.
        :param search_session:
        :return:
        """
        with self.lock:
            self.search_session = search_session

    def register_on_process_finished(self, func):
        self.on_process_finished = func

    def process_finished(self, wrapped_result):
        search_request = wrapped_result[0]
        crawl_result = wrapped_result[1]

        if crawl_result is None:

            # we need to mark as invalid the result in order to be reprocessed.
            self.search_session.reset_search_request(search_request)
            logging.info("[{}%] Request {} could not be retrieved. Reseted.".format(
                self.search_session.get_completion_progress(), search_request))

        else:

            search_request.associate_result(crawl_result)
            # Log to session
            self.search_session.add_history_entry(search_request)

            logging.info("[{}%] Results for request {} retrieved: {}.".format(
                self.search_session.get_completion_progress(), search_request, len(crawl_result)
            ))

        global_status.update_proc_progress("Retrieving data from search engines...",
                                    self.search_session.get_completion_progress())

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

    def stop(self, wait_for_finish=True):
        print("Stop of crawler service requested")
        logging.info("Crawler stopped from digesting requests.")
        Service.stop(self, wait_for_finish)

    def __internal_thread__(self):
        Service.__internal_thread__(self)
        do_sleep = 0

        while not self.__get_stop_flag__():

            with self.lock:
                if self.processing_queue.qsize() < self.processes:

                    try:
                        search_request = self.search_session.pop_new_search_request()
                    except:
                        search_request = None

                    if search_request:
                        self.queue_request(search_request)

                    else:
                        do_sleep = 0.5

                else:
                    do_sleep = 0.3

            with self.ping_lock:
                self.pong = self.ping

            if do_sleep:
                sleep(do_sleep)
                do_sleep = 0

            self.process_queue()

        self.__set_status__(SERVICE_STOPPED)
