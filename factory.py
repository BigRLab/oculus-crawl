#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging

import sys

from main.dataset.dataset_factory import DatasetFactory

__author__ = "Ivan de Paz Centeno"


root = logging.getLogger()
root.setLevel(logging.INFO)
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
root.addHandler(ch)

########
# This line is enough for the process to work.
# The factory is now listening on port 24005.
#
dataset_factory = DatasetFactory()

logging.info("********************************")
logging.info("Listening on port {}".format(dataset_factory.get_port()))
logging.info("********************************")
