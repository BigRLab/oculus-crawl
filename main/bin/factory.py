#!/usr/bin/env python
# -*- coding: utf-8 -*-
from flask import Flask
import sys
from main.controllers.controller_factory import ControllerFactory
from main.search_engine import yahoo_images, bing_images, google_images, howold_images, flickr_images
from main.dataset.dataset_factory import DatasetFactory
from main.service.global_status import global_status


__author__ = "Ivan de Paz Centeno"

def force_exit():
    global_status.stop()
    exit(-1)

def print_usage():
    """
    Prints the usage pattern.
    """
    print("Usage: factory HOST -p PORT -d DATASETS_DESTINATION_URI")

def get_options():
    """
    Retrieves the argument options from the input.
    :return:
    """
    options = {}

    try:
        required_options = ["host", "port", "datasets_destination_uri"]
        key = None

        for arg in sys.argv[1:]:
            if key is not None:
                options[key] = arg
                key = None
                continue

            if arg == "-p":
                key = "port"
            elif arg == "-d":
                key = "datasets_destination_uri"
            elif arg == "-h":
                print_usage()
                force_exit()
            else:
                options['host'] = arg

            if key in options:
                raise Exception("Error: option {} redifined.".format(key))

        if "port" not in options:
            options['port'] = 24005

        if "datasets_destination_uri" not in options:
            options['datasets_destination_uri'] = "/var/www/html/datasets/"

        for key in required_options:
            if key not in options:
                raise Exception("Missing option: {}.".format(key))

    except Exception as ex:
        print("Error: {}".format(ex))
        force_exit()

    return options


options = get_options()

app = Flask(__name__)

dataset_factory = DatasetFactory(publish_dir=options['datasets_destination_uri'])

controller_factory = ControllerFactory(app, dataset_factory=dataset_factory)

# Now we set up which controllers do we want to hold in our APP.
controller_factory.dataset_factory_controller()
controller_factory.search_session_controller()

app.run(host=options['host'], port=int(options['port']), threaded=True)