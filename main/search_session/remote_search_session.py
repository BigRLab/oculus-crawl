#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import logging

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
        self.__send_request__({
            'action': 'append_search_requests',
            'search_requests': [request.serialize() for request in search_requests]
        })

        response = self.__get_response__()

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
        self.__send_request__({
            'action': 'pop_request'
        })

        response = self.__get_response__()

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

        self.__send_request__({
            'action': 'add_to_history',
            'search_request': search_request.serialize()
        })

        response = self.__get_response__()

        if 'result' in response:
            result = response['result'] == 'Done'
        else:
            result = False

        return result

    def size(self):
        self.__send_request__({
            'action': 'size'
        })

        response = self.__get_response__()

        if 'result' in response:
            result = response['result']
        else:
            result = False

        return result

    def get_completion_progress(self):
        self.__send_request__({
            'action': 'get_completion_progress'
        })

        response = self.__get_response__()

        if 'result' in response:
            result = response['result']
        else:
            result = False

        return result

    def save_session(self, filename, dump_in_progress_as_pending=True):
        """
        Saves the current session in a file in JSON format.
        :param dump_in_progress_as_pending:
        :param filename: URI to the file.
        :return: True if could be saved. False otherwise.
        """
        self.__send_request__({
            'action': 'get_session_data',
            'dump_in_progress_as_pending': dump_in_progress_as_pending
        })

        serial = self.__get_response__()
        if 'result' in serial:
            serial = serial['result']

        logging.info(serial)
        try:
            assert ('search_requests' in serial)
            assert ('search_history' in serial)

            with open(filename, 'w') as outfile:
                json.dump(serial, outfile)

            result = True
            logging.info("Session file saved in {}".format(filename))
        except:
            result = False
            logging.info("Could not save the file because of remote malformed response")

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

            self.__send_request__({
                'action': 'set_session_data',
                'data': data,
                'load_in_progress_as_pending': load_in_progress_as_pending
            })

            response = self.__get_response__()

            if 'result' in response:
                result = response['result']
            else:
                result = False

        except:
            result = False

        if result:
            logging.info("Session loaded from file {}".format(filename))
        else:
            logging.info("Session couldn't be loaded!")

        return result