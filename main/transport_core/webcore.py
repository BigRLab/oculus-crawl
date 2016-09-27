#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = "Ivan de Paz Centeno"
import logging
from pyvirtualdisplay import Display
from selenium.webdriver import Firefox


class WebCore(object):
    """
    Represents the transport core for the surface web.
    """

    def __init__(self):
        self.virtual_browser_display = Display(visible=False, size=(800, 600))
        self.virtual_browser = Firefox()
        self.virtual_browser.set_window_position(-1000, -1000)

    def get(self, url):
        logging.info("Get started")
        self.virtual_browser.get(url)
        logging.info("Get finished")

    def get_elements_html_by_class(self, class_name):
        logging.info("Getting elements by class {}".format(class_name))
        elements_by_class = self.virtual_browser.find_elements_by_class_name(class_name)
        logging.info("Retrieved {} elements of class {}".format(len(elements_by_class), class_name))

        result = [element.get_attribute('innerHTML') for element in elements_by_class]
        return result

    def get_elements_html_by_tag(self, tag_name):
        return [element.get_attribute('innerHTML') for element in
                self.virtual_browser.find_elements_by_tag_name(tag_name)]

    def __del__(self):
        self.virtual_browser.close()
        self.virtual_browser_display.stop()
