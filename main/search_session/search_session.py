#!/usr/bin/env python
# -*- coding: utf-8 -*-
import time

__author__ = "Ivan de Paz Centeno"


class SearchSession(object):
    def __init__(self):
        self.start_time = time.time()
        self.search_requests = {} # hash: request
        self.search_history = {}
        self.finish_time = 0

    def append_search_requests(self, search_requests = None):
        if not search_requests:
            search_requests = []

        for search in search_requests:
            if search.__hash__() not in self.search_history:
                self.search_requests[search.__hash__()] = search

    def pop_new_search_request(self):
        if len(self.search_requests) > 0:
            search_request = self.search_requests.popitem()[1]
        else:
            search_request = None

        return search_request

    def add_entry(self, search_request):
        self.search_history[search_request.__hash__()] = search_request

    def size(self):
        return len(self.search_requests)

    def get_start_time(self):
        return self.start_time

    def get_completion_progress(self):
        return int(len(self.search_history) / (len(self.search_requests) + len(self.search_history)) * 100)

    def mark_as_finished(self):
        self.finish_time = time.time()

    def get_time_employed(self):
        elapsed = self.finish_time
        if elapsed == 0:
            elapsed = time.time()

        return elapsed - self.start_time

    def reset(self):
        new_request_list = list(self.search_history.values())
        self.start_time = time.time()
        self.finish_time = 0
        self.search_history = {}
        self.append_search_requests(new_request_list)