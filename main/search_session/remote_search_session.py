#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import logging

import time

from main.search_session.search_request import SearchRequest
from main.service.service_client import ServiceClient

__author__ = "Ivan de Paz Centeno"


class RemoteSearchSession(ServiceClient):
    """
    Represents a search session that is hosted somewhere.
    It acts as a proxy class, allowing the retrieval or appending of new search requests.
    """

    def __init__(self, remote_host, remote_port=24001):
        ServiceClient.__init__(self, remote_host, remote_port)

    def append_search_requests(self, search_requests=None):
        """
        Adds a batch of search requests to the session.
        If a crawler is working over this session at the moment that elements are appended, the crawler will
        process them on the fly.
        :param search_requests:
        :return:
        """
        response = self._send_request({
            'action': 'append_search_requests',
            'search_requests': [request.serialize() for request in search_requests]
        })

        if 'result' in  response:
            result = response['result'] == 'Done'
        else:
            result = False

        return result

    def pop_new_search_request(self):
        """
        Retrieves a search request from the list of search requests of the search session.
        :return:
        """
        response = self._send_request({
            'action': 'pop_request'
        })

        if 'result' in response and response['result']:
            result = SearchRequest.deserialize(response['result'])
        else:
            result = None

        return result

    def add_history_entry(self, search_request):
        """
        Registers an entry in the session history.
        This means that the search request is already processed.

        If the search request is in the in-progress list, it will be automatically removed from that list.
        :param search_request:
        :return:
        """

        response = self._send_request({
            'action': 'add_to_history',
            'search_request': search_request.serialize()
        })

        if 'result' in response:
            result = response['result'] == 'Done'
        else:
            result = False

        return result

    def size(self):
        response = self._send_request({
            'action': 'size'
        })

        if 'result' in response:
            result = response['result']
        else:
            result = False

        return result

    def get_completion_progress(self):
        try:
            response = self._send_request({
                'action': 'get_completion_progress'
            })

            if 'result' in response:
                result = response['result']
            else:
                result = False
        except Exception as ex:
            logging.info("Error while get_completion_progress from search_session stub: {}".format(ex))
            result = False

        return result

    def save_session(self, filename, dump_in_progress_as_pending=True):
        """
        Saves the current session in a file in JSON format.
        :param dump_in_progress_as_pending:
        :param filename: URI to the file.
        :return: True if could be saved. False otherwise.
        """
        response = self._send_request({
            'action': 'get_session_data',
            'dump_in_progress_as_pending': dump_in_progress_as_pending
        })

        if 'result' in response:
            response = response['result']

        logging.info(response)
        try:
            assert ('search_requests' in response)
            assert ('search_history' in response)

            with open(filename, 'w') as outfile:
                json.dump(response, outfile)

            result = True
            logging.info("Session file saved in {}".format(filename))

        except Exception as ex:
            result = False
            logging.info("Could not save the file because of remote malformed response. Reason: {}".format(ex))

        return result

    def load_session(self, filename, load_in_progress_as_pending=True):
        """
        Loads the current session from a file.
        :param load_in_progress_as_pending:
        :param filename: URI to the file.
        :return: True if could be loaded. False otherwise.
        """
        try:
            with open(filename, 'r') as infile:
                data = json.load(infile)

            response = self._send_request({
                'action': 'set_session_data',
                'data': data,
                'load_in_progress_as_pending': load_in_progress_as_pending
            })

            if 'result' in response:
                result = response['result']
                logging.info("Session loaded from file {}".format(filename))
            else:
                result = False
                logging.info("Couldn't load session. Reason: remote endpoint didn't return a well-formatted response.")

        except Exception as ex:
            result = False
            logging.info("Session couldn't be loaded. Reason: {}".format(ex))


        return result

    def get_history(self):
        """
        Retrieves the history from the session.
        :return: The history data
        """
        logging.info("Retrieving history...")
        response = self._send_request({
            'action': 'get_history'
        })
        logging.info("Retrieved: {}".format(response))

        result = {}

        if 'result' in response and response['result']:
            history_search_requests = [SearchRequest.deserialize(serial) for serial in response['result']]

            for search_request in history_search_requests:
                result[search_request.__hash__()] = search_request

        return result

    def wait_for_finish(self):
        """
        Freezes the thread until the process is finished.
        """
        while self.get_completion_progress() != 100:
            time.sleep(1)
