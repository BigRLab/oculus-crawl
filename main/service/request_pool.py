#!/usr/bin/env python
# -*- coding: utf-8 -*-
from multiprocessing import Manager
from multiprocessing.pool import Pool
from queue import Empty
from time import sleep
import logging

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

    search_engine_proto = search_request.get_search_engine_proto()

    # This way we cache the search_engine between requests in the same thread.
    if not search_engine or search_engine.__class__ != search_engine_proto:
        search_engine = search_engine_proto()

    return [queue_element[0], search_engine.retrieve(search_request)]


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
        self.stop_processing = False

    @staticmethod
    def _init_pool_worker(time_secs_between_requests):
        """
        Initializes the worker thread. Each worker of the pool has its own firefox and display instance.
        :param self:
        :return:
        """
        global wait_seconds_between_requests

        wait_seconds_between_requests = time_secs_between_requests

    def queue_request(self, search_request):
        """
        put a search request in the search request queue.
        :param search_request: search request instance
        :return:
        """
        logging.info("Queued request {}.".format(search_request))
        self.processing_queue.put([search_request])

    def process_queue(self):
        """
        Processes the queue until all the processes are busy or until the queue is empty
        :return:
        """

        while self.processes_free > 0 and not self.stop_processing:
            try:
                logging.info(
                    "Processing queue with {} free processes (stop flag is {}).".format(self.processes_free,
                                                                                                    self.stop_processing))

                self.processes_free -= 1
                queue_element = self.processing_queue.get(False)
                result = self.pool.apply_async(process, args=(queue_element,), callback=self._process_finished)

            except Empty:
                logging.info("No elements queued.")

                return

    def _process_finished(self, wrapped_result):
        """
        Callback when the worker's thread is finished.
        This is an internal callback.
        It will call process_finished method if available to notify the result.
        :param wrapped_result:
        :return:
        """
        self.processes_free += 1
        self.process_queue()

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