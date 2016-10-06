#!/usr/bin/env python
# -*- coding: utf-8 -*-
from urllib.request import urlopen, Request
from multiprocessing import Manager
from multiprocessing.pool import Pool
from queue import Empty
from time import sleep
from mimetypes import guess_extension
from os.path import splitext
from urllib.parse import urlparse
import logging

__author__ = "Ivan de Paz Centeno"

wait_seconds_between_requests = 0


def inferre_extension(download_url):
    try:
        inferred_extension = splitext(urlparse(download_url).path)[1]

    except Exception as ex:
        inferred_extension = None
        logging.info("Couldn't inferre the extension from the url {}.".format(download_url))

    return inferred_extension


def process(queue_element):
    """
    Generic process function.
    The pool process is going to execute this function on its own thread.
    :param queue_element: element extracted from the queue.
    :return: search engine request result.
    """
    global wait_seconds_between_requests

    #print("wait seconds: {}".format(wait_seconds_between_requests))
    if wait_seconds_between_requests > 0:
        sleep(wait_seconds_between_requests)

    # We fetch the search variables from the queue element
    download_url = queue_element[0]
    logging.info("Processing url {}.".format(download_url))

    try:
        req = Request(download_url, headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.84 Safari/537.36'})
        source = urlopen(req)
        data = source.read()
        headers = source.info()

        if 'Content-Type' in headers:
            extension = guess_extension(headers['Content-Type'])
        else:
            extension = None

        if not extension:
            extension = inferre_extension(download_url)

        logging.info("Downloaded url {} (mime-type-extension: {})".format(download_url, extension))

    except Exception as e:
        data = None
        extension = ""
        logging.info("Failed to download {}; reason: {}".format(download_url, str(e)))

    return [download_url, data, extension]


class FetchPool(object):
    """
    Pool processes for downloading images.
    Allows concurrently download of images
    """

    def __init__(self, pool_limit=10, time_secs_between_requests=None):
        # 10 concurrent downloads is a good ammount (pool_limit)
        self.manager = Manager()
        self.processing_queue = self.manager.Queue()

        self.pool = Pool(processes=pool_limit, initializer=self._init_pool_worker,
                         initargs=[time_secs_between_requests])
        self.processes_free = pool_limit
        self.stop_processing = False

    @staticmethod
    def _init_pool_worker(time_secs_between_requests=0):
        """
        Initializes the worker thread.
        :param self:
        :return:
        """
        global wait_seconds_between_requests

        if not time_secs_between_requests:
            time_secs_between_requests = 0

        wait_seconds_between_requests = time_secs_between_requests

    def queue_download(self, url):
        """
        put a download request in the download queue.
        :param url: download url
        :return:
        """
        logging.info("Queued url to download {}.".format(url))
        self.processing_queue.put([url])
        self.process_queue()

    def process_queue(self):
        """
        Processes the queue until all the processes are busy or until the queue is empty
        :return:
        """

        while self.processes_free > 0 and not self.stop_processing:
            try:
                queue_element = self.processing_queue.get(False)
                logging.info(
                    "Processing queue with {} free processes (stop flag is {}).".format(self.processes_free,
                                                                                        self.stop_processing))
                self.processes_free -= 1
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