#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import logging
import time

from main.search_session.search_request import SearchRequest
from main.service.service import Service, SERVICE_STOPPED
from main.service.socket_interface import SocketInterface

__author__ = "Ivan de Paz Centeno"


class SearchSession(Service, SocketInterface):
    """
    This search session is a way to centralize all the crawlers. This way we don't need to know where is each crawler
    and we only need to know where is this session. All the crawled data is going to end up here.
    """

    def __init__(self, host="0.0.0.0", port=24001, autostart=True, zmq_context=None):
        Service.__init__(self)
        SocketInterface.__init__(self, host, port, zmq_context=zmq_context)

        self.start_time = time.time()
        self.search_requests = {}  # hash: request
        self.search_history = {}
        self.search_in_progress = {}
        self.finish_time = 0
        if autostart:
            self.start()

    def append_search_requests(self, search_requests=None):
        """
        Adds a batch of search requests to the session.
        If a crawler is working over this session at the moment that elements are appended, the crawler will
        process them on the fly.
        :param search_requests:
        :return:
        """
        if not search_requests:
            search_requests = []

        for search in search_requests:
            if search.__hash__() not in self.search_history and search.__hash__() not in self.search_in_progress:
                self.search_requests[search.__hash__()] = search

    def pop_new_search_request(self):
        """
        When a search request is poped out from the session history, it is stored as a search request in progress.
        This will help us to track the search request progress status in the future.
        :return:
        """
        if len(self.search_requests) > 0:
            search_request = self.search_requests.popitem()[1]
            self.search_in_progress[search_request.__hash__()] = search_request
        else:
            search_request = None

        return search_request

    def add_history_entry(self, search_request):
        """
        Registers an entry in the session history.
        This means that the search request is already processed.

        If the search request is in the in-progress list, it will be automatically removed from that list.
        :param search_request:
        :return:
        """
        self.search_history[search_request.__hash__()] = search_request
        if search_request.__hash__() in self.search_in_progress:
            self.search_in_progress.pop(search_request.__hash__())

    def size(self):
        """
        Returns the amount of search requests queued to be processed.
        :return:
        """
        return len(self.search_requests)

    def get_start_time(self):
        """
        Returns the time at which the session was started.
        """
        return self.start_time

    def get_completion_progress(self):
        """
        :return: the % of completion done.
        """
        if len(self.search_requests) + len(self.search_history) == 0:
            result = 0
        else:
            result = int(len(self.search_history) / (
            len(self.search_requests) + len(self.search_in_progress) + len(self.search_history)) * 100)

        return result

    def get_history(self):
        """

        :return: the search history dictionary. The search requests are indexed by their hash.
        """
        return self.search_history

    def mark_as_finished(self):
        """
        Marks teh current session as finished.
        :return: The time at which the session finished.
        """
        self.finish_time = time.time()

    def get_time_employed(self):
        """
        :return: the time spent in the session until now, unless it is marked as finished.
        """
        elapsed = self.finish_time
        if elapsed == 0:
            elapsed = time.time()

        return elapsed - self.start_time

    def wait_for_finish(self):
        """
        Freezes the thread until the process is finished.
        """
        while self.get_completion_progress() != 100:
            time.sleep(1)

    def reset(self):
        """
        Resets the current search session. The history requests are set as pending requests after this method is
        invoked. The search requests in progress are left as is since it means that there could be crawlers currently
        processing them.
        :return:
        """
        new_request_list = list(self.search_history.values())  # + list(self.search_in_progress.values())
        self.start_time = time.time()
        self.finish_time = 0
        self.search_history = {}
        self.append_search_requests(new_request_list)

    def save_session(self, filename, dump_in_progress_as_pending=True):
        """
        Saves the current session in a file in JSON format.
        :param dump_in_progress_as_pending:
        :param filename: URI to the file.
        :return: True if could be saved. False otherwise.
        """
        serial = self._serialize(dump_in_progress_as_pending)

        try:
            with open(filename, 'w') as outfile:
                json.dump(serial, outfile, indent=4, sort_keys=True)

            result = True
            logging.info("Session file saved in {}".format(filename))
        except Exception as ex:
            result = False
            logging.info("Could not save the session: {}".format(ex))

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

            self._deserialize(data, load_in_progress_as_pending)
            result = True
            logging.info("Session loaded from file {}".format(filename))
        except:
            logging.info("Could session not load from file")
            result = False

        return result

    def _serialize(self, dump_in_progress_as_pending=True):
        """
        Serializes the current search session in a JSON format.
        :param dump_in_progress_as_pending: if set to True, it will set all the in-progress requests as pendin-
        search requests
        :return: the serialized version of this session.
        """
        data = {'search_requests': [self.search_requests[search_request_hash].serialize() for search_request_hash in
                                    self.search_requests],
                'search_history': [self.search_history[search_request_hash].serialize() for search_request_hash in
                                   self.search_history]}

        if dump_in_progress_as_pending:
            data['search_requests'] += [self.search_in_progress[search_request_hash].serialize() for search_request_hash
                                        in self.search_in_progress]
            logging.info("Search-request in progress dumped as new search_request: {}".format(data))
        else:
            data['search_in_progress'] = [self.search_in_progress[search_request_hash].serialize() for
                                          search_request_hash in self.search_in_progress]
            logging.info("Search-request in progress dumped: {}".format(data))

        return data

    def _deserialize(self, data, dump_in_progress_as_pending=True):
        """
        Builds the search requests for this session from the given JSON data.
        :param data: JSON data of a serialized search session.
        :param dump_in_progress_as_pending: If set to true, it will set all the in-progress requests as
        pendin-search requests.
        :return:
        """

        assert ('search_requests' in data)
        assert ('search_history' in data)

        self.search_requests = {}
        self.search_history = {}
        self.search_in_progress = {}

        for search_request_json in data['search_requests']:
            search_request = SearchRequest.deserialize(search_request_json)
            self.search_requests[search_request.__hash__()] = search_request

        for search_request_json in data['search_history']:
            search_request = SearchRequest.deserialize(search_request_json)
            self.search_history[search_request.__hash__()] = search_request

        if 'search_in_progress' in data and dump_in_progress_as_pending:
            for search_request_json in data['search_in_progress']:
                search_request = SearchRequest.deserialize(search_request_json)
                self.search_in_progress[search_request.__hash__()] = search_request

    def __internal_thread__(self):
        Service.__internal_thread__(self)
        SocketInterface.init_socket(self)

        while not self.__get_stop_flag__():

            [request, identity, exit_requested] = self.get_new_request()

            if exit_requested:

                self.__set_stop_flag__()

            elif 'action' in request:

                #logging.info(request)

                {
                    'append_search_requests': self._append_search_requests,
                    'size': self._size,
                    'pop_request': self._pop_request,
                    'add_to_history': self._add_to_history,
                    'get_completion_progress': self._get_completion_progress,
                    'get_session_data': self._get_session_data,
                    'set_session_data': self._set_session_data,
                    'get_history': self._get_history
                }[request['action']](identity, request)

        SocketInterface.terminate(self)

        self.__set_status__(SERVICE_STOPPED)

    def _size(self, identity, request):
        SocketInterface.send_response(self, identity, {'result': self.size()})

    def _pop_request(self, identity, request):

        new_request = self.pop_new_search_request()

        if new_request:
            new_request = new_request.serialize()

        SocketInterface.send_response(self, identity, {'result': new_request})

    def _append_search_requests(self, identity, request):
        search_requests = [SearchRequest.deserialize(search_request) for search_request in request['search_requests']]
        self.append_search_requests(search_requests)
        SocketInterface.send_response(self, identity, {'result': "Done"})

    def _add_to_history(self, identity, request):
        search_request = SearchRequest.deserialize(request['search_request'])
        self.add_history_entry(search_request)
        SocketInterface.send_response(self, identity, {'result': "Done"})

    def _get_completion_progress(self, identity, request):
        SocketInterface.send_response(self, identity, {'result': self.get_completion_progress()})

    def _get_session_data(self, identity, request):
        try:
            assert ('dump_in_progress_as_pending' in request)

            dump_in_progress_as_pending = request['dump_in_progress_as_pending']
        except:
            logging.info("Session request is malformed. Sending it anyway.")
            dump_in_progress_as_pending = True

        SocketInterface.send_response(self, identity, {'result': self._serialize(dump_in_progress_as_pending)})

    def _set_session_data(self, identity, request):
        try:
            assert ('load_in_progress_as_pending' in request)
            assert ('data' in request)

            load_in_progress_as_pending = request['load_in_progress_as_pending']
            data = request['data']
            self._deserialize(data, load_in_progress_as_pending)
            result = True
        except:
            logging.info("Session update is malformed. Discarding it.")
            result = False

        SocketInterface.send_response(self, identity, {'result': result})

    def _get_history(self, identity, request):
        logging.info("History requested.")
        SocketInterface.send_response(self, identity, {'result':
                                                       [self.search_history[search_request_hash].serialize() for
                                                        search_request_hash in
                                                        self.search_history]})

        logging.info("History sent.")

    def __del__(self):
        self.stop()