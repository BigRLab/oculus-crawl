#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import os

import sys
from time import sleep, time

from main.dataset.remote_dataset_factory import RemoteDatasetFactory
from main.search_engine.bing_images import BingImages
from main.search_engine.flickr_images import FlickrImages
from main.search_engine.google_images import GoogleImages
from main.search_engine.yahoo_images import YahooImages
from main.search_session.search_request import SearchRequest
from main.service.status import SERVICE_CREATED_DATASET, get_status_name, SERVICE_STATUS_UNKNOWN, SERVICE_RUNNING, \
    get_status_by_name

__author__ = "Ivan de Paz Centeno"

try:
    os.mkdir("backups/")
except:
    pass

root = logging.getLogger()
root.setLevel(logging.INFO)
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
root.addHandler(ch)

remote_dataset_factory = RemoteDatasetFactory("http://localhost:24005/")

# We want now to inject some search.

#dataset_name = "test_"+str(time())
dataset_name = "12yo"

# Print iterations progress
def print_progress(iteration, total, prefix='', suffix='', decimals=1, bar_length=100):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        barLength   - Optional  : character length of bar (Int)
    """
    format_str = "{0:." + str(decimals) + "f}"
    percents = format_str.format(100 * (iteration / float(total)))
    filled_length = int(round(bar_length * iteration / float(total)))
    bar = '' * filled_length + '-' * (bar_length - filled_length)
    sys.stdout.write('\r%s |%s| %s%s %s' % (prefix, bar, percents, '%', suffix)),
    if iteration == total:
        sys.stdout.write('\n')
    sys.stdout.flush()


def generate_search_requests(keywords, append_adjetives=None, portraits=False):
    """
    Generates a list of search-requests with the specified keywords in the 3 most used search-engines
    (yahoo, google and bing).

    :param keywords:
    :param portraits:
    :return: search requests array to append to the factory.
    """
    #search_engines = [YahooImages, GoogleImages, BingImages]
    search_engines = [YahooImages, GoogleImages]

    options = {}

    if portraits:
        options['face'] = 'true'

    keywords_list = [keywords]

    if append_adjetives:
        keywords_list = ["{} {}".format(keywords, adjetive) for adjetive in append_adjetives]

    return [SearchRequest(adjetived_keywords, options, search_engine) for search_engine in search_engines for
            adjetived_keywords in keywords_list]

try:
    remote_dataset_factory.create_dataset(dataset_name)

    keywords_list = [
        "12 year old boy", "12 year old girl"
    ]

    '''"2 years old boy", "2 years old girl",
    "3 years old boy", "3 years old girl",
    "4 years old boy", "4 years old girl",
    "5 years old boy", "5 years old girl",
    "6 years old boy", "6 years old girl",
    "7 years old boy", "7 years old girl",
    "8 years old boy", "8 years old girl",
    "9 years old boy", "9 years old girl",
    "10 years old boy", "10 years old girl",
    "11 years old boy", "11 years old girl",
    "12 years old boy", "12 years old girl"'''
    adjetives = ["sad", "happy", "small", "big", "crying", "cute", "smiling", "moving", "dancing", "cousin", "funny", "clever", ""]
    search_requests = []

    for keywords in keywords_list:
        search_requests += generate_search_requests(keywords, adjetives, False)

    for search_request in search_requests:
        print ("{}: {}".format(search_request.get_search_engine_proto() ,search_request.get_words()))

    remote_session = remote_dataset_factory.get_session_from_dataset_name(dataset_name)
    remote_session.append_search_requests(search_requests)

    status = SERVICE_STATUS_UNKNOWN
    previous_status = SERVICE_STATUS_UNKNOWN

    progress_completed = {
        SERVICE_RUNNING: True,
        previous_status: True,
    }

    time_passed = 0

    logging.info("*****************************")
    logging.info("Dataset creation requested with name {}".format(dataset_name))
    logging.info("*****************************")

    completed = False

    while status != SERVICE_CREATED_DATASET:
        percent_data = remote_dataset_factory.get_dataset_builder_percent(dataset_name)
        status = get_status_by_name(percent_data['status'])

        if status == SERVICE_STATUS_UNKNOWN and 'percent' not in percent_data:

            if previous_status != SERVICE_STATUS_UNKNOWN:
                # It has finished faster than our poll time between status
                status = SERVICE_CREATED_DATASET
                percent = 100

            else:
                raise Exception("The dataset dissapeared from the list.")

        else:
            percent = percent_data['percent']

        if status not in progress_completed:
            progress_completed[status] = False

        status_changed = status != previous_status

        if status_changed:
            if not progress_completed[previous_status]:
                print_progress(100, 100, get_status_name(previous_status), "Completed", bar_length=50)
                progress_completed[previous_status] = True

            previous_status = status

        if percent > -1 and not progress_completed[status]:
            print_progress(percent, 100, get_status_name(status), "Complete", bar_length=50)
            progress_completed[status] = percent == 100

        sleep(1)
        time_passed += 1

        if not completed:
            completed = remote_session.get_completion_progress() == 100

            if time_passed % 180 == 0:
                remote_session.save_session("backups/backup_{}_{}.json".format(dataset_name, remote_session.get_completion_progress()))

except Exception as ex:
    logging.info("Error: {}".format(ex))
