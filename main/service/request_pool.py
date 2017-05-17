#!/usr/bin/env python
# -*- coding: utf-8 -*-

from multiprocessing import Manager
from multiprocessing.pool import Pool
from queue import Empty
from threading import Lock
from time import sleep

import logging

from main.service.global_status import global_status

__author__ = "Ivan de Paz Centeno"

search_engine = None
wait_seconds_between_requests = 0


def process(queue_element):
    """
    Generic process function.
    The pool process is going to execute this function on its own thread.
    :param queue_element: element extracted from the queue.
    :return: search engine request result.
    """
    global search_engine, wait_seconds_between_requests

    sleep(wait_seconds_between_requests)

    # We fetch the search variables from the queue element
    search_request = queue_element[0]
    logging.info("Processing request {}.".format(search_request))

    global_status.update_proc("Processing request \"{}\" from {}".format(search_request.get_words(),
                                                                  search_request.get_search_engine_proto().__name__))

    search_engine_proto = search_request.get_search_engine_proto()

    # This way we cache the search_engine between requests in the same thread.
    if not search_engine or search_engine.__class__ != search_engine_proto:
        search_engine = search_engine_proto()

    try:

        retrieved_result = search_engine.retrieve(search_request)

    except Exception as ex:

        retrieved_result = None

    return [search_request, retrieved_result]


class RequestPool(object):
    """
    Pool processes for search engine requests.
    Allows to process requests by using a defined search engine, in parallel
    """

    def __init__(self, pool_limit=1, time_secs_between_requests=None):

        self.manager = Manager()

        self.processing_queue = self.manager.Queue()

        self.pool = Pool(processes=pool_limit, initializer=self._init_pool_worker,
                         initargs=[time_secs_between_requests])

        self.processes_free = pool_limit
        self._stop_processing = False
        self.lock_process_variable = Lock()

    @staticmethod
    def _init_pool_worker(time_secs_between_requests):
        """
        Initializes the worker thread. Each worker of the pool has its own firefox and display instance.
        :return:
        """
        global wait_seconds_between_requests

        wait_seconds_between_requests = time_secs_between_requests

    def do_stop(self):
        with self.lock_process_variable:
            self._stop_processing = True

    def _stop_requested(self):
        with self.lock_process_variable:
            stop_requested = self._stop_processing

        return stop_requested

    def queue_request(self, search_request):
        """
        put a search request in the search request queue.
        :param search_request: search request instance
        :return:
        """
        logging.info("Queued request {}.".format(search_request))
        self.processing_queue.put([search_request])

    def get_processes_free(self):

        with self.lock_process_variable:
            processes_free = self.processes_free

        return processes_free

    def take_process(self):

        with self.lock_process_variable:
            self.processes_free -= 1

    def process_freed(self):

        with self.lock_process_variable:
            self.processes_free += 1

    def process_queue(self):
        """
        Processes the queue until all the processes are busy or until the queue is empty
        :return:
        """

        while self.get_processes_free() > 0 and not self._stop_requested():
            try:
                queue_element = self.processing_queue.get(False)
                logging.info(
                    "Processing queue with {} free processes (stop flag is {}).".format(self.get_processes_free(),
                                                                                        self._stop_requested()))
                self.take_process()

                result = self.pool.apply_async(process, args=(queue_element,), callback=self._process_finished)

            except Empty:
                logging.info("No elements queued.")
                break

    def _process_finished(self, wrapped_result):
        """
        Callback when the worker's thread is finished.
        This is an internal callback.
        It will call process_finished method if available to notify the result.
        :param wrapped_result:
        :return:
        """
        self.process_freed()

        if hasattr(self, 'process_finished'):
            self.process_finished(wrapped_result)

        return None

    def terminate(self):
        """
        Finishes safely the pool.
        :return:
        """
        self.pool.terminate()
        self.pool.join()
