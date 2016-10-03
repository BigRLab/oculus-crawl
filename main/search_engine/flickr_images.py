#!/usr/bin/env python
# -*- coding: utf-8 -*-
from PIL import ImageFile

from main.transport_core.webcore import WebCore
import urllib
import urllib.request
import logging
from bs4 import BeautifulSoup

__author__ = "Ivan de Paz Centeno"

MAX_IMAGES_PER_REQUEST = 750    # This will take between 20 and 30 minutes


class FlickrImages(object):
    """
    Search engine that retrieves information of images from the flickr images search engine.
    """

    def __init__(self):
        self.transport_core = WebCore(window_size=(1300, 1500))  # It is the preferable and the default transport core for Flickr.

    def retrieve(self, search_request):
        """
        Performs a retrieval from the flickr images (by tags) given the search request info.
        :param search_request: A search request instance filled with the keywords and the options for the desired
         search. The following options are currently accepted:
        :return:
        """
        # This way we cache the transport core.
        if not self.transport_core or search_request.get_transport_core_proto() != self.transport_core.__class__:
            self.transport_core = search_request.get_transport_core_proto()()
            logging.debug("Transport core created from proto.")

        logging.info("Retrieving image links from request {}.".format(search_request))
        return self._retrieve_image_links_data(search_request.get_words(), search_request.get_options())

    def _retrieve_image_links_data(self, search_words, search_options):
        # Initialization
        result = []

        # TODO: add search options for this search engine. They can be encoded in the URL.
        url = "https://www.flickr.com/search/?tags="+search_words+"&media=photos"
        logging.info("Built url ({}) for request.".format(url))

        self.transport_core.get(url)

        self.transport_core.wait_for_elements_from_class("photo-list-photo-view")

        # The iteration starts after clicking the first element. We can't access all the desired information
        # from the main list, we need to preview each element one by one. If not, only URLs are available.
        self.transport_core.click_button_by_class("photo-list-photo-view")

        logging.info("Get done. Loading elements JSON")

        count = 0
        while count < MAX_IMAGES_PER_REQUEST:
            image_json = self._retrieve_image_json()

            if 'url' in image_json:
                result.append(image_json)

            self.transport_core.click_button_by_class("navigate-next")

        return result

    def _retrieve_image_json(self):

        image_json = {}

        if len(self.transport_core.get_elements_html_by_class("more-info")) == 0:
            main_photo = BeautifulSoup(self.transport_core.get_elements_html_by_class("main-photo", False)[0], 'html.parser').find()
            image_json['url'] = self._prepend_http_protocol(main_photo["src"], is_ssl=True)

            image_json['width'], image_json['height'] = self._get_url_size(image_json['url'])

            tags = [BeautifulSoup(element, 'html.parser').find() for element in self.transport_core.get_elements_html_by_class("tag", False)]
            tags = [element.find_all("a")[1] for element in tags]

            date_taken = BeautifulSoup(self.transport_core.get_elements_html_by_class("date-taken-label", False)[0], 'html.parser').find()["title"]
            tag_description = [tag["title"] for tag in tags]

            image_json['desc'] = "{};{}".format(date_taken, ";".join(tag_description))

        # ELSE: We skip this iteration because it is spam

        return image_json

    @staticmethod
    def _get_url_size(url):
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

    @staticmethod
    def _prepend_http_protocol(url, is_ssl=False):
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

