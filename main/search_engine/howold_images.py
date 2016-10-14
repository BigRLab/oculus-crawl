#!/usr/bin/env python
# -*- coding: utf-8 -*-
from main.search_engine.search_engine import SEARCH_ENGINES, SearchEngine
import urllib
import logging
from bs4 import BeautifulSoup

__author__ = "Ivan de Paz Centeno"


class HowOldImages(SearchEngine):
    """
    Search engine that retrieves information of images in the howold webpage.
    """

    def retrieve(self, search_request):
        """
        Performs a retrieval from HowOld given the search request info.
        :param search_request: A search request instance filled with the keywords and the options for the desired
         search. The following options are currently accepted:

        :return:
        """
        # This way we cache the transport core.
        if not self.transport_core or search_request.get_transport_core_proto() != self.transport_core.__class__:
            self.transport_core = search_request.get_transport_core_proto()()
            logging.info("Transport core created from proto.")

        logging.debug("Retrieving image links from request {}.".format(search_request))
        return self._retrieve_image_links_data(search_request.get_words(), search_request.get_options())

    def _retrieve_image_links_data(self, search_words, search_options):

        url = "https://how-old.net/?q={}".format(
            urllib.parse.quote_plus(search_words))

        logging.info("Built url ({}) for request.".format(url))

        self.transport_core.get(url)

        self.transport_core.wait_for_elements_from_class("ImageSelector")

        logging.info("Get done. Loading elements JSON")

        image_list_html = self.transport_core.get_elements_html_by_id("imageList", innerHTML=False)[0]

        img_tag_list = BeautifulSoup(image_list_html, 'html.parser').find().find_all("img")

        json_elements = [self._build_json_for(image_tag, search_words) for image_tag in img_tag_list]

        logging.info("Retrieved {} elements".format(len(json_elements)))
        return json_elements

    def _build_json_for(self, image_tag, search_words):
        url = image_tag['src']
        image_size = self._get_url_size(url)

        return {'url': image_tag['src'], 'width': image_size[0], 'height': image_size[1], 'desc': search_words,
                'source': 'howold'}


# Register the class to enable deserialization.
SEARCH_ENGINES[str(HowOldImages)] = HowOldImages
