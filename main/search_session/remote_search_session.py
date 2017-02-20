#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import logging
import time
import requests

from main.search_session.search_request import SearchRequest


__author__ = "Ivan de Paz Centeno"


class RemoteSearchSession():
    """
    Represents a search session that is hosted somewhere.
    It acts as a proxy class, allowing the retrieval or appending of new search requests.
    """

    def __init__(self, backend_url):
        """
        Initializes the search session for a given URL.
        :param backend_url: url of a search session to wrap.
        """
        self.backend_url = backend_url

    def append_search_requests(self, search_requests):
        """
        Adds a batch of search requests to the session.
        If a crawler is working over this session at the moment that elements are appended, the crawler will
        process them on the fly.
        :param search_requests:
        :return:
        """
        url = "{}/search-request".format(self.backend_url)

        response = requests.put(url, json={'search_requests': [request.serialize() for request in search_requests]})

        if response.status_code != 200:
            raise Exception("Backend ({}) for session is returning a bad response!".format(url))

    def reset_search_request(self, search_request):
        """
        Resets the specified search request. If this session has this request under the on progress queue, it will
        become as available again. If it doesn't contain this search request, it will be appended as a normal add().
        :param search_request:
        :return:
        """

        url = "{}/search-request".format(self.backend_url)

        response = requests.patch(url, json={'search_request': search_request.serialize()})

        if response.status_code != 200:
            raise Exception("Backend ({}) for session is returning a bad response!".format(url))

    def pop_new_search_request(self):
        """
        Retrieves a search request from the list of search requests of the search session.
        :return:
        """

        url = "{}/search-request".format(self.backend_url)

        response = requests.get(url)

        if response.status_code == 200:
            result = SearchRequest.deserialize(response.json())

        elif response.status_code == 404:
            result = None

        else:
            raise Exception("Backend ({}) for session is returning a bad response!".format(url))

        return result

    def add_history_entry(self, search_request):
        """
        Registers an entry in the session history.
        This means that the search request is already processed.

        If the search request is in the in-progress list, it will be automatically removed from that list.
        :param search_request:
        :return:
        """

        url = "{}/history".format(self.backend_url)

        response = requests.put(url, json={'search_request': search_request.serialize()})

        if response.status_code != 200:
            raise Exception("Backend ({}) for session is returning a bad response!".format(url))

    def size(self):
        """
        Retrieves the size of the session (number of elements in the search-requests queue).
        :return:
        """
        url = "{}/size".format(self.backend_url)

        response = requests.get(url)

        if response.status_code != 200:
            raise Exception("Backend ({}) for session is returning a bad response!".format(url))

        size = int(str(response.text))

        return size

    def get_completion_progress(self):
        """
        Retrieves the completion progress for the wrapped search session.
        :return:
        """
        url = "{}/completion-progress".format(self.backend_url)

        response = requests.get(url)

        if response.status_code != 200:
            raise Exception("Backend ({}) for session is returning a bad response! ({})".format(url, response))

        completed_percent = int(str(response.text))

        return completed_percent

    def save_session(self, filename, dump_in_progress_as_pending=True):
        """
        Saves the current session in a file in JSON format.
        :param dump_in_progress_as_pending:
        :param filename: URI to the file.
        :return: True if could be saved. False otherwise.
        """
        url = "{}/data".format(self.backend_url)

        response = requests.get(url, params={'dump_in_progress_as_pending': dump_in_progress_as_pending})

        if response.status_code != 200:
            raise Exception("Backend ({}) for session is returning a bad response!".format(url))

        data = response.json()

        if 'result' in data:
            data = data['result']

        try:
            assert ('search_requests' in data)
            assert ('search_history' in data)

            with open(filename, 'w') as outfile:
                json.dump(data, outfile)

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
        url = "{}/data".format(self.backend_url)

        try:
            with open(filename, 'r') as infile:
                data = json.load(infile)

            response = requests.put(url, params={'load_in_progress_as_pending': load_in_progress_as_pending}, json={"data":data})

            if response.status_code != 200:
                raise Exception("Backend ({}) for session is returning a bad response ({})!".format(url, response.json()['message']))

            result = True
            logging.info("Session loaded from file {}".format(filename))

        except Exception as ex:

            result = False
            print("Session couldn't be loaded. Reason: {}".format(ex))

        return result

    def get_history(self):
        """
        Retrieves the history from the session.
        :return: The history data
        """

        url = "{}/history".format(self.backend_url)

        response = requests.get(url)

        if response.status_code != 200:
            raise Exception("Backend ({}) for session is returning a bad response!".format(url))

        history = response.json()

        result = []

        if 'result' in history and history['result']:
            history_search_requests = [SearchRequest.deserialize(serial) for serial in history['result']]

            for search_request in history_search_requests:
                result[search_request.__hash__()] = search_request

        return result

    def wait_for_finish(self):
        """
        Freezes the thread until the process is finished.
        """
        while self.get_completion_progress() != 100:
            time.sleep(1)
