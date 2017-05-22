#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import logging
import os
import random

import sys
from time import sleep, time
import datetime
from main.dataset.remote_dataset_factory import RemoteDatasetFactory
from main.search_engine.bing_images import BingImages
from main.search_engine.google_images import GoogleImages
from main.search_engine.yahoo_images import YahooImages
from main.search_session.search_request import SearchRequest
from main.service.global_status import global_status
from main.service.status import SERVICE_CREATED_DATASET, get_status_name, SERVICE_STATUS_UNKNOWN, SERVICE_RUNNING, \
    get_status_by_name

__author__ = "Ivan de Paz Centeno"


def force_exit():
    global_status.stop()
    exit(-1)


def print_usage():
    """
    Prints the usage pattern.
    """
    print("Usage: ocrawl URL -n \"DATASET_NAME\" -s \"SEARCH_KEYWORDS:[ADJETIVE LIST TO COMBINE]\" -s \"SEARC...\"  [-b BACKUP_FOLDER] [-t BACKUP_TIME_SECONDS] [-v]")


def enable_verbose():
    """
    Enables the logging messages output to console.
    :return:
    """
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    root.addHandler(ch)


def get_options():
    """
    Retrieves the argument options from the input.
    :return:
    """
    options = {}

    try:
        required_options = ["url", "dataset_name", "search_keywords", "backup_folder", "backup_time_seconds"]
        key = None

        for arg in sys.argv[1:]:
            if key is not None:

                if key == "search_keywords":
                    options[key][arg.split(":")[0]] = arg.split(":")[1]
                else:
                    options[key] = arg

                key = None
                continue

            if arg == "-n":
                key = "dataset_name"
            elif arg == "-s":
                key = "search_keywords"
            elif arg == "-b":
                key = "backup_folder"
            elif arg == "-t":
                key = "backup_time_seconds"
            elif arg == "-v":
                # Let's enable the debug messages
                enable_verbose()
            elif arg == "-h":
                print_usage()
                force_exit()
            else:
                options['url'] = arg

            if key == "search_keywords" and key not in options:
                options[key] = {}

            if key in options and key != "search_keywords":
                raise Exception("Error: option {} redifined.".format(key))

        if "dataset_name" not in options:
            options['dataset_name'] = "noname_"+datetime.datetime.fromtimestamp(time()).strftime('%Y%m%d-%H-%M-%S')

        if "backup_time_seconds" not in options:
            options['backup_time_seconds'] = "180" # 3 minutes

        if "backup_folder" not in options:
            options['backup_folder'] = "/backups"

        for key in required_options:
            if key not in options:
                raise Exception("Missing option: {}.".format(key))

    except Exception as ex:
        print("Error: {}".format(ex))
        force_exit()

    return options


options = get_options()

# A backup folder, it is important.
try:
    os.mkdir(os.path.join(options['datasets_destination_uri'],"backups/"))
except:
    pass

remote_dataset_factory = RemoteDatasetFactory(options['url'])

# We want now to inject some search.

#dataset_name = "test_"+str(time())
dataset_name = options['dataset_name']
backup_time_seconds = int(options['backup_time_seconds'])

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
    bar = '#' * filled_length + '-' * (bar_length - filled_length)
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
    search_engines = [YahooImages, GoogleImages] # Bing is failing by now, removed from the list.

    _options = {}

    if portraits:
        _options['face'] = 'true'

    keywords_list = [keywords]

    if append_adjetives:
        keywords_list = ["{} {}".format(keywords, adjetive) for adjetive in append_adjetives]

    return [SearchRequest(adjetived_keywords, _options, search_engine) for search_engine in search_engines for
            adjetived_keywords in keywords_list]

try:
    remote_dataset_factory.create_dataset(dataset_name)

    search_keywords_dict = options['search_keywords']
    search_requests = []

    for search_keywords, adjetives_str in search_keywords_dict.items():
        try:
            adjetives = json.loads(adjetives_str)
            search_requests += generate_search_requests(search_keywords, adjetives, False)
        except:
            print("Adjetives do not have a valid format. Must be JSON-compliant.")
            exit(-1)

    random.shuffle(search_requests)

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
    print("*****************************")
    print("Dataset creation requested with name {}".format(dataset_name))
    print("*****************************")

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

            if time_passed % backup_time_seconds == 0:
                remote_session.save_session(
                    os.path.join(options['backup_folder'],
                                 "backup_{}_{}.json".format(dataset_name, remote_session.get_completion_progress())
                                 )
                )

    print("Dataset is now hosted by the factory. Visit the factory public interface to access it.")
except Exception as ex:
    logging.info("Error: {}".format(ex))

global_status.stop()
