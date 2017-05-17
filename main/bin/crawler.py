#!/usr/bin/env python
# -*- coding: utf-8 -*-

import signal
import sys
from main.crawling_process import CrawlingProcess
from main.search_engine import yahoo_images, bing_images, flickr_images, google_images, howold_images
from main.service.global_status import global_status

__author__ = "Ivan de Paz Centeno"



def get_options():
    """
    Retrieves the argument options from the input.
    :return:
    """
    try:
        required_options = ["url", "workers", "wait_time_between_tries"]
        options = {}
        key = ""

        for arg in sys.argv:
            if arg == "-h":
                print("Usage: crawler URL -w WORKERS_COUNT -t TIME_WAIT_BETWEEN_TRIES_IN_SECONDS")
            elif arg == "-w":
                key = "workers"
            elif arg == "-t":
                key = "wait_time_between_tries"
            else:
                key = "url"

            if key in options:
                raise Exception("Error: option {} redifined.".format(key))

        if "workers" not in options:
            options['workers'] = 1

        if "wait_time_between_tries" not in options:
            options['wait_time_between_tries'] = 1

        if not all(key in options for key in required_options):
            raise Exception("Missing options {}.".format([key for key in required_options not in options]))

    except Exception as ex:
        print("Error: {}".format(ex))
        sys.exit(-1)


options = get_options()

def signal_handler(signal, frame):
    pass

signal.signal(signal.SIGINT, signal_handler)

crawling_process = CrawlingProcess(options['url'], options['workers'], options['time_wait_between_tries'])

crawling_process.start()

signal.pause()

crawling_process.stop()
global_status.stop()