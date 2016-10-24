#!/usr/bin/env python
# -*- coding: utf-8 -*-
from main.search_engine.search_engine import SEARCH_ENGINES, SearchEngine
from main.transport_core.webcore import WebCore
import urllib
import urllib.request
import logging
from bs4 import BeautifulSoup

__author__ = "Ivan de Paz Centeno"

#MAX_IMAGES_PER_REQUEST = 350    # This will take between 20 and 30 minutes
MAX_IMAGES_PER_REQUEST = 25
MAX_NAVIGATE_TRIES = 10


class FlickrImages(SearchEngine):
    """
    Search engine that retrieves information of images from the flickr images search engine.
    """

    def retrieve(self, search_request):
        """
        Performs a retrieval from the flickr images (by tags) given the search request info.
        :param search_request: A search request instance filled with the keywords and the options for the desired
         search. The following options are currently accepted:
        :return:
        """
        print("[FLICKR] Retrieve() entered.")
        # This way we cache the transport core.
        if not self.transport_core or search_request.get_transport_core_proto() != self.transport_core.__class__:
            self.transport_core = search_request.get_transport_core_proto()()
            logging.debug("Transport core created from proto.")
        print("[FLICKR] Retrieve() first condition passed.")

        logging.info("Retrieving image links from request {}.".format(search_request))
        return self._retrieve_image_links_data(search_request.get_words(), search_request.get_options())

    def _retrieve_image_links_data(self, search_words, search_options):
        # Initialization
        result = []
        print("[FLICKR] Retrieve_image_links_data() entered.")

        # TODO: add search options for this search engine. They can be encoded in the URL.
        url = "https://www.flickr.com/search/?tags={}&media=photos".format(search_words)
        logging.info("Built url ({}) for request.".format(url))

        self.transport_core.get(url)
        print("[FLICKR] transport_core get invoked.")

        self.transport_core.manual_wait_for_element_from_class("photo-list-photo-view")
        print("[FLICKR] waited successfully for the elements of class 'photo-list-photo-view'")

        # The iteration starts after clicking the first element. We can't access all the desired information
        # from the main list, we need to preview each element one by one. If not, only URLs are available.
        self.transport_core.click_button_by_class("photo-list-photo-view")
        print("[FLICKR] Clicked button of class 'photo-list-photo-view'")

        logging.info("Get done. Loading elements JSON")

        count = 0
        while count < MAX_IMAGES_PER_REQUEST:
            print("[FLICKR] waiting for elements of class '.navigate-next'")
            self.transport_core.manual_wait_for_element_from_class("navigate-next")
            print("[FLICKR] stopped waiting for elements of class '.navigate-next'")
            image_json = self._retrieve_image_json(search_words)

            if 'url' in image_json:
                result.append(image_json)

            logging.info("FLICKR - Progress: {}%".format(int(len(result) / MAX_IMAGES_PER_REQUEST * 100)))
            #self.transport_core.click_button_by_class("navigate-next")
            self._navigate_next()
            count += 1

        return result

    def _navigate_next(self):
        href_retrieved = ""
        tries = 0
        while not href_retrieved and tries < MAX_NAVIGATE_TRIES:
            elements = self.transport_core.get_elements_html_by_class("navigate-next", innerHTML=False)

            if not len(elements):
                return

            element_bs = [BeautifulSoup(element, 'html.parser').find() for element in elements]

            href_list = [element['href'] for element in element_bs]

            for href in href_list:
                if len(href) > len("https://"):
                    href_retrieved = href
                    break

            tries += 1

        if href_retrieved:
            print("getting {}".format(href_retrieved))
            self.transport_core.get(href_retrieved)
            print("[FLICKR] waiting for elements of class '.navigate-next'")
            self.transport_core.manual_wait_for_element_from_class("navigate-next")
            print("[FLICKR] stopped waiting for elements of class '.navigate-next'")

    def _retrieve_image_json(self, search_words):
        print("[FLICKR] _retrieve_image_json() called.")

        image_json = {}

        print("[FLICKR] _retrieve_image_json() waiting for 'follow-view'")
        self.transport_core.manual_wait_for_element_from_class("follow-view")
        print("[FLICKR] _retrieve_image_json() finished waiting for 'follow-view'")

        #if len(self.transport_core.get_elements_html_by_class("more-info")) == 0:
        if len(self.transport_core.get_elements_html_by_class("follow-view")) > 0:

            print("[FLICKR] _retrieve_image_json() Seems that we can take the element from the DOM")
            main_photo = BeautifulSoup(self.transport_core.get_elements_html_by_class("main-photo", False)[0], 'html.parser').find()
            image_json['url'] = self._prepend_http_protocol(main_photo["src"], is_ssl=True)

            image_json['width'], image_json['height'] = self._get_url_size(image_json['url'])

            print("[FLICKR] _retrieve_image_json() Before getting tags {}".format(image_json))
            tags = [BeautifulSoup(element, 'html.parser').find() for element in self.transport_core.get_elements_html_by_class("tag", False)]
            tags = [element.find_all("a")[1] for element in tags]

            date_taken = BeautifulSoup(self.transport_core.get_elements_html_by_class("date-taken-label", False)[0], 'html.parser').find()["title"]
            tag_description = [tag["title"] for tag in tags]

            image_json['desc'] = "{};{};{}".format(date_taken, ";".join(tag_description), search_words)
            image_json['source'] = "flickr"
            print("[FLICKR] _retrieve_image_json() After getting tags {}".format(image_json))

        # ELSE: We skip this iteration because it is spam

        return image_json


# Register the class to enable deserialization.
SEARCH_ENGINES[str(FlickrImages)] = FlickrImages