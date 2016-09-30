#!/usr/bin/env python
# -*- coding: utf-8 -*-
import html

from main.transport_core.webcore import WebCore
import urllib
import urllib.parse as urlparse
import json
import logging
from bs4 import BeautifulSoup

__author__ = "Ivan de Paz Centeno"

MAX_IMAGES_PER_REQUEST = 750
MAX_SCROLL_NO_UPDATE_IMAGES_THRESHOLD = 3


class YahooImages(object):
    """
    Search engine that retrieves information of images from the yahoo images search engine.
    """

    def __init__(self):
        self.transport_core = WebCore()  # It is the preferable and the default transport core for Yahoo.

    def retrieve(self, search_request):
        """
        Performs a retrieval from the yahoo images given the search request info.
        :param search_request: A search request instance filled with the keywords and the options for the desired
         search. The following options are currently accepted:
            'face' -> Select the face option as a search filter. Yahoo images contains a portrait option in the search
                    that this flag enables. It will result in images of faces related with the given keywords.
        :return:
        """
        # This way we cache the transport core.
        if not self.transport_core or search_request.get_transport_core_proto() != self.transport_core.__class__:
            self.transport_core = search_request.get_transport_core_proto()()
            logging.debug("Transport core created from proto.")

        logging.info("Retrieving image links from request {}.".format(search_request))
        return self._retrieve_image_links_data(search_request.get_words(), search_request.get_options())

    def _retrieve_image_links_data(self, search_words, search_options):

        url = "https://es.images.search.yahoo.com"
        logging.info("Built url ({}) for request.".format(url))

        self.transport_core.get(url)

        # Since yahoo builds the url dynamically per client request, we need to pass through their ring.
        # We fill the search input box
        text = urllib.parse.quote_plus(search_words)
        self.transport_core.send_text_to_input_by_id("yschsp", text)

        # Then we click it
        self.transport_core.click_button_by_class("ygbt")

        if 'face' in search_options:
            # We enable the portrait option if needed.
            self.transport_core.click_button_by_class("portrait")

        self._cache_all_page()

        logging.info("Get done. Loading elements JSON")

        ld_elements = [BeautifulSoup(html_element, 'html.parser').find() for html_element in
                       self.transport_core.get_elements_html_by_class("ld ", False)]

        result = [self._build_json_for(element) for element in ld_elements]

        logging.info("Retrieved {} elements".format(len(result)))
        return result

    def _cache_all_page(self):
        """
        This search engine adds content dynamically when you scroll down the page.
        We are interested in all the content we can get from the same page, so we
        simulate scroll downs until no more content is added.
        :return:
        """
        previous_percent = -1
        current_percent = 0
        finished = False
        no_update_count = 0

        while not finished:
            logging.info("images cached previously: {}, images cached currently: {}".format(previous_percent, current_percent))

            if current_percent > MAX_IMAGES_PER_REQUEST or no_update_count > MAX_SCROLL_NO_UPDATE_IMAGES_THRESHOLD:
                finished = True
                continue

            if previous_percent == current_percent:
                no_update_count +=1
                self.transport_core.click_button_by_class("more-res")
            else:
                no_update_count = 0

            previous_percent = current_percent
            self.transport_core.scroll_to_bottom()
            elements = self.transport_core.get_elements_html_by_class("ld ")
            current_percent = len(elements)

    @staticmethod
    def _prepend_http_protocol(url):
        if url.lower()[:7] == "http://" or url.lower()[:8] == "https://":
            prepend_text = ""
        else:
            prepend_text = "http://"

        return prepend_text + url

    def _build_json_for(self, element):

        if element.has_attr('data'):
            data = element["data"]
        else:
            data = None

        if data:
            json_data = json.loads(html.unescape(data))
            result = {'url': self._prepend_http_protocol(json_data['iurl']), 'width': json_data['w'],
                      'height': json_data['h'],
                      'desc': json_data['alt']}
        else:
            link = element.find("a")
            if link:
                href = link["href"]
                parsed_href = urlparse.parse_qs(urlparse.urlparse(href).query)
                result = {'url': self._prepend_http_protocol(parsed_href['imgurl'][0]), 'w': parsed_href['w'][0],
                          'h': parsed_href['h'][0], 'desc': parsed_href['name'][0]}
            else:
                result = {}

        return result
