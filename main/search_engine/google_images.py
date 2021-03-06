#!/usr/bin/env python
# -*- coding: utf-8 -*-
from main.search_engine.search_engine import SEARCH_ENGINES, SearchEngine
from main.service.global_status import global_status
from main.transport_core.webcore import WebCore
import urllib
import json
import logging

__author__ = "Ivan de Paz Centeno"


class GoogleImages(SearchEngine):
    """
    Search engine that retrieves information of images in the google images tab from google.
    """

    def retrieve(self, search_request):
        """
        Performs a retrieval from the google images given the search request info.
        :param search_request: A search request instance filled with the keywords and the options for the desired
         search. The following options are currently accepted:
            'face' -> Select the face option as a search filter. Google images contains a face option in the search that
                    this flag enables. It will result in images of faces related with the given keywords.
        :return: A json wrapping all the result retrieved from the search_request.
        """
        # This way we cache the transport core.

        if not self.transport_core or search_request.get_transport_core_proto() != self.transport_core.__class__:
            self.transport_core = search_request.get_transport_core_proto()()
            logging.info("Transport core created from proto.")

        global_status.update_proc_progress("{} ({})".format(self.__class__.__name__, search_request.get_words()), 0)

        logging.debug("Retrieving image links from request {}.".format(search_request))
        return self._retrieve_image_links_data(search_request.get_words(), search_request.get_options())

    def _retrieve_image_links_data(self, search_words, search_options):

        url = "https://www.google.es/search?q={}&site=webhp&source=Lnms&tbm=isch".format(
            urllib.parse.quote_plus(search_words))

        if 'face' in search_options:
            url += '&tbs=itp:face'
        logging.info("Built url ({}) for request.".format(url))
        global_status.update_proc_progress("{} ({}) *Built url ({}) for request*".format(self.__class__.__name__,
                                                                                  search_words, url), 0)

        global_status.update_proc_progress("{} ({}) *Retrieving URL*".format(self.__class__.__name__, search_words), 0)

        self.transport_core.get(url)
        global_status.update_proc_progress("{} ({}) *Retrieved URL*".format(self.__class__.__name__, search_words), 0)

        self._cache_all_page(search_words)

        logging.info("Get done. Loading elements JSON")
        global_status.update_proc_progress("{} ({}) *Generating JSON*".format(self.__class__.__name__, search_words), 100)

        json_elements = [json.loads(element) for element in self.transport_core.get_elements_html_by_class("rg_meta")]

        global_status.update_proc_progress("{} ({}) *Generated content for {} elements*".format(self.__class__.__name__,
                                                                                         search_words, len(json_elements)), 100)
        logging.info("Retrieved {} elements".format(len(json_elements)))
        return [{'url': image['ou'], 'width': image['ow'], 'height': image['oh'], 'desc': image['pt'],
                 'searchwords':search_words,
                 'source':'google'} for image in json_elements]

    def _cache_all_page(self, search_words):
        """
        This search engine adds content dynamically when you scroll down the page.
        We are interested in all the content we can get from the same page, so we
        simulate scroll downs until no more content is added.
        :return:
        """
        # We know maximum is 400 for google

        previous_percent = -1
        current_percent = 0

        while previous_percent < current_percent:
            previous_percent = current_percent
            self.transport_core.scroll_to_bottom()
            elements = self.transport_core.get_elements_html_by_class("rg_meta")
            current_percent = len(elements)

            global_status.update_proc_progress("{} ({}) *Caching page*".format(self.__class__.__name__, search_words),
                                        current_percent, max=400)

# Register the class to enable deserialization.
SEARCH_ENGINES[str(GoogleImages)] = GoogleImages