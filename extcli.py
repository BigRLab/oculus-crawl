#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging

import sys
from time import sleep, time

from main.dataset.remote_dataset_factory import RemoteDatasetFactory
from main.search_engine.flickr_images import FlickrImages
from main.search_engine.google_images import GoogleImages
from main.search_engine.yahoo_images import YahooImages
from main.search_session.search_request import SearchRequest
from main.service.status import SERVICE_CREATED_DATASET, get_status_name, SERVICE_STATUS_UNKNOWN, SERVICE_RUNNING, \
    get_status_by_name

__author__ = "Ivan de Paz Centeno"

root = logging.getLogger()
root.setLevel(logging.INFO)
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
root.addHandler(ch)

remote_dataset_factory = RemoteDatasetFactory("localhost")

# We want now to inject some search.

dataset_name = "test_"+str(time())


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

try:
    if not remote_dataset_factory.create_dataset(dataset_name):
        raise Exception("Dataset request could not be created on the factory.")

    remote_session = remote_dataset_factory.get_session_from_dataset_name(dataset_name)
    remote_session.append_search_requests([SearchRequest("1 yo old", {'face': True}, YahooImages)])

    status = SERVICE_STATUS_UNKNOWN
    previous_status = SERVICE_STATUS_UNKNOWN

    progress_completed = {
        SERVICE_RUNNING: True,
        previous_status: True,
    }

    logging.info("*****************************")
    logging.info("Dataset creation requested with name {}".format(dataset_name))
    logging.info("*****************************")

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

except Exception as ex:
    logging.info("Error: {}".format(ex))
