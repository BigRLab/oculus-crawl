#!/usr/bin/env python
# -*- coding: utf-8 -*-
from main.transport_core.webcore import WebCore
import urllib
import json
import logging

__author__ = "Ivan de Paz Centeno"


class GoogleImages(object):

    def __init__(self):
        self.transport_core = WebCore()     # It is the preferable and the default transport core for Google.

    def retrieve(self, search_request):

        # This way we cache the transport core.
        if not self.transport_core or search_request.get_transport_core_proto() != self.transport_core.__class__:
            self.transport_core = search_request.get_transport_core_proto()()
            logging.info("Transport core created from proto.")

        logging.info("Retrieving image links from request {}.".format(search_request))
        return self._retrieve_image_links_data(search_request.get_words(), search_request.get_options())

    def _retrieve_image_links_data(self, search_words, search_options):

        url = "https://www.google.es/search?q={}&site=webhp&source=Lnms&tbm=isch".format(
            urllib.parse.quote_plus(search_words))

        if 'face' in search_options:
            url += '&tbs=itp:face'
        logging.info("Built url ({}) for request.".format(url))

        self.transport_core.get(url)

        logging.info("Get done. Loading elements JSON")

        json_elements = [json.loads(element) for element in self.transport_core.get_elements_html_by_class("rg_meta")]

        logging.info("Retrieved {} elements".format(len(json_elements)))
        return [{'url': image['ou'], 'width': image['ow'], 'height': image['oh'], 'desc': image['pt']} for image
                in json_elements]

