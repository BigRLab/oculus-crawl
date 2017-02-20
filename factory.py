#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging

import sys

from flask import Flask

from main.controllers.controller_factory import ControllerFactory
from main.search_engine import yahoo_images, bing_images, google_images, howold_images, flickr_images
from main.dataset.dataset_factory import DatasetFactory

__author__ = "Ivan de Paz Centeno"


root = logging.getLogger()
root.setLevel(logging.INFO)
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
root.addHandler(ch)

#search_session = SearchSession(port=24010)
#search_session.stop()
#search_session2 = SearchSession(port=24010)
#search_session2.stop()

########
# This line is enough for the process to work.
# The factory is now listening on port 24005.
#
#dataset_factory = DatasetFactory()

#logging.info("********************************")
#logging.info("Listening on port {}".format(dataset_factory.get_port()))
#logging.info("********************************")

app = Flask(__name__)

dataset_factory = DatasetFactory()

controller_factory = ControllerFactory(app, dataset_factory=dataset_factory)

# Now we set up which controllers do we want to hold in our APP.
controller_factory.dataset_factory_controller()
controller_factory.search_session_controller()

app.run(host="localhost", port=24005, threaded=True)