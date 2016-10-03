#!/usr/bin/env python
# -*- coding: utf-8 -*-
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
    def __init__(self, host="0.0.0.0", port=24001, autostart=True):
        Service.__init__(self)
        SocketInterface.__init__(self, host, port)

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
        return len(self.search_requests)

    def get_start_time(self):
        return self.start_time

    def get_completion_progress(self):
        if len(self.search_requests) + len(self.search_history) == 0:
            result = 0
        else:
            result = int(len(self.search_history) / (len(self.search_requests) + len(self.search_in_progress) + len(self.search_history)) * 100)

        return result

    def get_history(self):
        return self.search_history

    def mark_as_finished(self):
        self.finish_time = time.time()

    def get_time_employed(self):
        elapsed = self.finish_time
        if elapsed == 0:
            elapsed = time.time()

        return elapsed - self.start_time

    def wait_for_finish(self):
        while self.get_completion_progress() != 100:
            time.sleep(1)

    def reset(self):
        new_request_list = list(self.search_history.values())
        self.start_time = time.time()
        self.finish_time = 0
        self.search_history = {}
        self.append_search_requests(new_request_list)

    def __internal_thread__(self):
        Service.__internal_thread__(self)
        SocketInterface.init_socket(self)

        while not self.__get_stop_flag__():

            [request, identity, exit_requested] = self.get_new_request()

            #logging.info(request)
            if exit_requested:

                self.__set_stop_flag__()

            elif 'action' in request:

                {
                    'append_search_requests': self._append_search_requests,
                    'size': self._size,
                    'pop_request': self._pop_request,
                    'add_to_history': self._add_to_history,
                    'get_completion_progress': self._get_completion_progress
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
