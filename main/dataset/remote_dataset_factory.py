#!/usr/bin/env python
# -*- coding: utf-8 -*-
import requests

from main.dataset.dataset import DATASET_TYPES
from main.dataset.generic_dataset import GenericDataset
from main.search_session.remote_search_session import RemoteSearchSession

__author__ = "Ivan de Paz Centeno"


class RemoteDatasetFactory():
    """
    Proxies a remote dataset in order to create/manipulate datasets.
    """

    def __init__(self, backend_url):
        """
        Initializer for the proxy.
        :param backend_url:
        """

        if backend_url[-1] == "/":
            backend_url = backend_url[:-1]

        self.backend_url = backend_url

    def get_dataset_builder_percent(self, name):
        """
        Retrieves the dataset build percent for the specified dataset name.
        :param name: name of the dataset to request the build percent .
        :return: a dictionary holding the status and the percentage of the status.
        """
        url = "{}/dataset/{}/progress".format(self.backend_url, name)

        response = requests.get(url)

        if response.status_code != 200:
            raise Exception("Backend ({}) for session is returning a bad response!".format(url))

        return response.json()

    def get_dataset_builder_names(self):
        """
        Returns a list of names of the dataset builders in progress.
        :return:
        """
        url = "{}/dataset/".format(self.backend_url)

        response = requests.get(url)

        if response.status_code != 200:
            raise Exception("Backend ({}) for session is returning a bad response!".format(url))

        response = response.json()

        if 'result' in response:
            result = response['result']
        else:
            raise Exception("Backend sent a malformed response when retrieving the dataset names.")

        return result

    def get_session_from_dataset_name(self, name):
        """
        Return the session attached to a dataset name
        :param name: name of the dataset to get the session from.
        :return:
        """
        url = "{}/dataset/{}/session".format(self.backend_url, name)
        return RemoteSearchSession(url)

    def remove_dataset_builder_by_name(self, name):
        """
        Removes the dataset_builder from the list
        :param name: name of the dataset to remove from the list
        :return:
        """
        url = "{}/dataset/{}/".format(self.backend_url, name)

        response = requests.delete(url)

        if response.status_code != 200:
            raise Exception("Backend ({}) for session is returning a bad response!".format(url))

    def create_dataset(self, name, dataset_type=GenericDataset):
        """
        Creates a new dataset builder and a search_session associated to it.
        The search session is created with the parameters
        By default, the dataset builder is stopped until at least one search request is appended.

        :return: True if it was successfully created. False otherwise.
        """
        inv_dataset_types = {v: k for k, v in DATASET_TYPES.items()}

        url = "{}/dataset/".format(self.backend_url)

        response = requests.put(url, params={'name': name, 'dataset_type': inv_dataset_types[dataset_type]})

        if response.status_code == 401:
            raise Exception("Name \"{}\" is already taken.".format(name))

        elif response.status_code != 200:
            raise Exception("Backend ({}) for session is returning a bad response!".format(url))
