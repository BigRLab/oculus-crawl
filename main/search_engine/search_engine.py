#!/usr/bin/env python
# -*- coding: utf-8 -*-
import urllib
from PIL import ImageFile
from main.transport_core.webcore import WebCore

__author__ = "Ivan de Paz Centeno"


class SearchEngine(object):

    def __init__(self):
        print("initializing")
        self.transport_core = WebCore()  # It is the preferable and the default transport core.
        print("initialized")

    def retrieve(self, search_request):
        """
        Processes the search request in order to retrieve the desired information.
        This is a virtual method and must be overriden.
        :param search_request:
        :return: The list of elements retrieved in JSON format.
        """

    def _get_url_size(self, url):
        """
        Request the size (width and height) of a URL image.
        :param url:
        :return: [width, height]
        """
        size = [0, 0]

        with urllib.request.urlopen(url) as file:
            image_parser = ImageFile.Parser()

            while True:
                data = file.read(1024)

                if not data:
                    break

                image_parser.feed(data)

                if image_parser.image:
                    size = image_parser.image.size
                    break

        return size

    def _prepend_http_protocol(self, url, is_ssl=False):
        if url.lower()[:7] == "http://" or url.lower()[:8] == "https://":
            prepend_text = ""
        elif url[:2] == "//":
            prepend_text = "http"

            if is_ssl:
                prepend_text += "s"

            prepend_text += ":"

        else:
            prepend_text = "http"

            if is_ssl:
                prepend_text += "s"

            prepend_text += "://"

        return prepend_text + url


# This file reflects the search engines available in the project. Useful for serialization/deserialization

# It is full of search-engine-proto-str : search-engine-proto lines
SEARCH_ENGINES = {}