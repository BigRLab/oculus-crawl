#!/usr/bin/env python
# -*- coding: utf-8 -*-
from main.search_engine.google_images import GoogleImages
from main.transport_core.webcore import WebCore

__author__ = "Ivan de Paz Centeno"


class SearchRequest(object):
    def __init__(self, words, options, search_engine_proto=GoogleImages, transport_core_proto=WebCore):
        self.words = words
        self.options = options
        self.transport_core_proto = transport_core_proto
        self.search_engine_proto = search_engine_proto

    def get_search_engine_proto(self):
        return self.search_engine_proto

    def get_transport_core_proto(self):
        return self.transport_core_proto

    def get_words(self):
        return self.words

    def get_options(self):
        return self.options

    def __str__(self):
        return "Words: \"{}\"; options: \"{}\" (search_engine: {}; transport core: {})".format(self.words,
                                                                                               self.options,
                                                                                               self.search_engine_proto,
                                                                                               self.transport_core_proto)

    def __hash__(self):
        return hash(self.__str__())
