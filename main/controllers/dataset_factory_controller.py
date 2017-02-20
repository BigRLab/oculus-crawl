#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
from flask import jsonify
from main.controllers.controller import route, Controller
from main.dataset.dataset import DATASET_TYPES
from main.dataset.generic_dataset import GenericDataset
from main.exceptions.invalid_request import InvalidRequest


__author__ = "Ivan de Paz Centeno"


class DatasetFactoryController(Controller):
    """
    Controller for /dataset URL
    """

    def __init__(self, flask_web_app, dataset_factory):
        """
        Constructor of the Session Controller.
        :param flask_web_app: web app from Flask already initialized.
        :param dataset_factory: factory of datasets to manipulate.
        """
        Controller.__init__(self, flask_web_app, dataset_factory)

        self.exposed_methods += [
            self.create_dataset,
            self.remove_dataset,
            self.get_running_datasets_list,
            self.get_dataset_progress,
        ]

        self._init_exposed_methods()

    @route("/dataset/", methods=['GET'])
    def get_running_datasets_list(self):
        """
        Retrieves the list of datasets currently being created.
        :return:
        """
        datasets_names = self.dataset_factory.get_dataset_builder_names()

        return jsonify({'result': [name for name in datasets_names]})

    @route("/dataset/<dataset_name>/progress", methods=['GET'])
    def get_dataset_progress(self, dataset_name):
        """
        Retrieves the progress of the specified dataset.
        :return:
        """

        status = self.dataset_factory.get_dataset_builder_percent(dataset_name)

        #if status['status'] == 'UNKNOWN':
        #    raise InvalidRequest("No dataset found in progress.", status_code=404)

        return jsonify(status)

    @route("/dataset/<dataset_name>/", methods=['DELETE'])
    def remove_dataset(self, dataset_name):
        """
        Removes the specified dataset.
        :return:
        """
        self.dataset_factory.remove_dataset_builder_by_name(dataset_name)

        return ""

    @route("/dataset/", methods=['PUT'])
    def create_dataset(self):
        """
        Creates a new dataset
        :return:
        """
        request = self._get_validated_request()

        if 'name' not in request:
            raise InvalidRequest("Name is required for a new dataset", status_code=400)

        name = request['name']

        if 'dataset_type' in request:
            if request['dataset_type'] not in DATASET_TYPES:
                raise InvalidRequest("The specified type of dataset is not valid.")

            dataset_type = DATASET_TYPES[request['dataset_type']]

        else:
            dataset_type = GenericDataset

        logging.info("Creating dataset with name {}".format(name))

        if self.dataset_factory.create_dataset(name, dataset_type=dataset_type):
            logging.info("Dataset with name {} initialized".format(name))
        else:
            logging.error("Dataset name {} is already taken".format(name))
            raise InvalidRequest("Name already taken.", 401)

        return ""
