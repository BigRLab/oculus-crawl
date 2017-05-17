#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Flask
import sys
from main.controllers.controller_factory import ControllerFactory
from main.search_engine import yahoo_images, bing_images, google_images, howold_images, flickr_images
from main.dataset.dataset_factory import DatasetFactory


__author__ = "Ivan de Paz Centeno"


def get_options():
    """
    Retrieves the argument options from the input.
    :return:
    """
    try:
        required_options = ["host", "port"]
        options = {}
        key = ""

        for arg in sys.argv:
            if arg == "-p":
                key = "port"
            elif arg == "-h":
                print("Usage: factory HOST -p PORT")
            else:
                key = "host"

            if key in options:
                raise Exception("Error: option {} redifined.".format(key))

        if "port" not in options:
            options['port'] = 24005

        if not all(key in options for key in required_options):
            raise Exception("Missing options {}.".format([key for key in required_options not in options]))

    except Exception as ex:
        print("Error: {}".format(ex))
        sys.exit(-1)


options = get_options()

app = Flask(__name__)

dataset_factory = DatasetFactory()

controller_factory = ControllerFactory(app, dataset_factory=dataset_factory)

# Now we set up which controllers do we want to hold in our APP.
controller_factory.dataset_factory_controller()
controller_factory.search_session_controller()

app.run(host=options['host'], port=int(options['port']), threaded=True)