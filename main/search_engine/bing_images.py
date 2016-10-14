#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
from main.search_engine.search_engine import SEARCH_ENGINES, SearchEngine

from main.transport_core.webcore import WebCore
import json
import logging
from bs4 import BeautifulSoup

__author__ = "Ivan de Paz Centeno"

#MAX_IMAGES_PER_REQUEST = 900
MAX_IMAGES_PER_REQUEST = 100
MAX_SCROLL_NO_UPDATE_IMAGES_THRESHOLD = 3


class BingImages(SearchEngine):
    """
    Search engine that retrieves information of images from the bing images search engine.
    """

    def retrieve(self, search_request):
        """
        Performs a retrieval from the bing images given the search request info.
        :param search_request: A search request instance filled with the keywords and the options for the desired
         search. The following options are currently accepted:
            'face' -> Select the face option as a search filter. Bing images contains a face only option in the search
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

        url = "http://www.bing.com/images/search?&q={}".format(search_words)

        # We enable the face option if needed.
        if 'face' in search_options:
            url += "&qft=+filterui:face-face"

        logging.info("Built url ({}) for request.".format(url))

        self.transport_core.get(url)
        self.transport_core.wait_for_elements_from_class("dg_u")

        self._cache_all_page()

        logging.info("Get done. Loading elements JSON")

        dg_u_elements = [BeautifulSoup(html_element, 'html.parser').find() for html_element in
                       self.transport_core.get_elements_html_by_class("dg_u", False)]

        logging.info("dg_elements loaded. Building json for each element...")

        result = [self._build_json_for(element, search_words) for element in dg_u_elements]

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
            else:
                no_update_count = 0

            previous_percent = current_percent
            #self.transport_core.scroll_to_bottom()
            elements = self.transport_core.get_elements_html_by_class("dg_u")
            current_percent = len(elements)

    def _build_json_for(self, element, search_words):
        element = element.find("a")
        #logging.info("Building for element {}".format(element))

        description = element['t1']
        size = element['t2']
        width = size.split(" ")[0]
        height = size.split(" ")[2]

        json_text = element['m']
        json_data = json.loads(re.sub('([{,])([^{:\s"]*):', lambda m: '{}"{}":'.format(m.group(1), m.group(2)),
                                      json_text))

        result = {'url': self._prepend_http_protocol(json_data['imgurl']),
                  'width': width,
                  'height': height,
                  'desc': description+";"+search_words,
                  'source': 'bing'}
        #logging.info("Result: {}".format(result))

        return result

# Register the class to enable deserialization.
SEARCH_ENGINES[str(BingImages)] = BingImages