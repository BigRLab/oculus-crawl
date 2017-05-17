#!/usr/bin/env python
# -*- coding: utf-8 -*-

import signal
import sys
from main.crawling_process import CrawlingProcess
from main.search_engine import yahoo_images, bing_images, flickr_images, google_images, howold_images
from main.service.global_status import global_status

__author__ = "Ivan de Paz Centeno"


def force_exit():
    global_status.stop()
    exit(-1)

def print_usage():
    """
    Prints the usage pattern.
    """
    print("Usage: crawler URL -w WORKERS_COUNT -t TIME_WAIT_BETWEEN_TRIES_IN_SECONDS")

def get_options():
    """
    Retrieves the argument options from the input.
    :return:
    """
    options = {}

    try:
        required_options = ["url", "workers", "wait_time_between_tries"]
        key = ""

        for arg in sys.argv:
            if key is not None:
                options[key] = arg
                key = None
                continue

            if arg == "-h":
                print_usage()
                force_exit()
            elif arg == "-w":
                key = "workers"
            elif arg == "-t":
                key = "wait_time_between_tries"
            else:
                options["url"] = arg

            if key in options:
                raise Exception("Error: option {} redifined.".format(key))

        if "workers" not in options:
            options['workers'] = 1

        if "wait_time_between_tries" not in options:
            options['wait_time_between_tries'] = 1

        for key in required_options:
            if key not in options:
                raise Exception("Missing option: {}.".format(key))

    except Exception as ex:
        print("Error: {}".format(ex))
        force_exit()

    return options


options = get_options()

def signal_handler(signal, frame):
    pass

signal.signal(signal.SIGINT, signal_handler)

crawling_process = CrawlingProcess(options['url'], options['workers'], float(options['wait_time_between_tries']))

crawling_process.start()

signal.pause()

crawling_process.stop()
global_status.stop()