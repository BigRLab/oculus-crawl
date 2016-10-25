#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging

from main.dataset.dataset import DATASET_TYPES
from main.dataset.generic_dataset import GenericDataset
from main.search_session.remote_search_session import RemoteSearchSession
from main.service.service_client import ServiceClient

__author__ = "Ivan de Paz Centeno"


class RemoteDatasetFactory(ServiceClient):

    def __init__(self, remote_host, remote_port=24005):
        ServiceClient.__init__(self, remote_host, remote_port)

    def get_dataset_builder_percent(self, name):
        """
        Adds a batch of search requests to the session.
        If a crawler is working over this session at the moment that elements are appended, the crawler will
        process them on the fly.
        :param search_requests:
        :return:
        """
        response = self._send_request({
            'action': 'get_dataset_progress_by_name',
            'name': name
        })

        if 'result' in response:
            result = response['result']
        else:
            if 'error' in response:
                error = response['error']
            else:
                error = "No response provided"

            logging.error("Could not retrieve the dataset builder progress: {}".format(error))
            result = -1

        return result

    def get_dataset_builder_names(self):
        """
        Returns a list of names of the dataset builders in progress.
        :return:
        """
        response = self._send_request({
            'action': 'get_dataset_names_list'
        })

        if 'result' in response:
            result = response['result']
        else:
            if 'error' in response:
                error = response['error']
            else:
                error = "No response provided"

            logging.error("Could not retrieve the datasets' names: {}".format(error))
            result = -1

        return result

    def get_dataset_builders_sessions(self):
        """
        Returns the list of the session attached to each of the dataset builders in progress.
        :return:
        """
        response = self._send_request({
            'action': 'get_sessions_from_datasets'
        })

        if 'result' in response:
            result = response['result']

            # We translate the serialized sessions into remote sessions
            new_result = {}

            for session_data in result:
                result = {'name': session_data['name'], 'session': RemoteSearchSession(session_data['host'],
                                                                                       session_data['port'])}

        else:
            if 'error' in response:
                error = response['error']
            else:
                error = "No response provided"

            logging.error("Could not retrieve the datasets' sessions: {}".format(error))
            result = -1

        return result

    def get_session_from_dataset_name(self, name):
        """
        Return the session attached to a dataset name
        :param name: name of the dataset to get the session from.
        :return:
        """
        response = self._send_request({
            'action': 'get_session_by_dataset_name',
            'name': name
        })

        if 'result' in response:
            session_data = response['result']

            result = RemoteSearchSession(session_data['host'], session_data['port'])

        else:
            if 'error' in response:
                error = response['error']
            else:
                error = "No response provided"

            logging.error("Could not retrieve the dataset session from name '{}': {}".format(name, error))
            result = None

        return result

    def remove_dataset_builder_by_name(self, name):
        """
        Removes the dataset_builder from the list
        :param name: name of the dataset to remove from the list
        :return:
        """
        response = self._send_request({
            'action': 'remove_dataset_by_name',
            'name': name
        })

        if 'result' in response:
            result = response['result'] == 'Done'
        else:
            if 'error' in response:
                error = response['error']
            else:
                error = "No response provided"

            logging.error("Could not remove the dataset: {}".format(error))
            result = False

        return result

    def create_dataset(self, name, host="0.0.0.0", port=None, dataset_type=GenericDataset):
        """
        Creates a new dataset builder and a search_session associated to it.
        The search session is created with the parameters
        By default, the dataset builder is stopped until at least one search request is appended.

        :param host: host for the search session. Crawlers will seek for this session's search requests on this host.
                    If host is not provided, it will fall back to all the interfaces.
        :param port: port for the search session. Crawlers will seek for this session's search requests on this port.
                    If port is not provided, it will fall back to a random free port.
        :return: the created dataset_builder.
        """
        inv_dataset_types = {v: k for k, v in DATASET_TYPES.items()}

        response = self._send_request({
            'action': 'create_dataset',
            'name': name,
            'host': host,
            'port': port,
            'dataset_type': inv_dataset_types[dataset_type]
        })

        if 'result' in response:
            result = response['result'] == 'Done'
        else:
            if 'error' in response:
                error = response['error']
            else:
                error = "No response provided"

            logging.error("Could not create the dataset: {}".format(error))
            result = False

        return result
