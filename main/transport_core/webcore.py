#!/usr/bin/env python
# -*- coding: utf-8 -*-
from main.transport_core.transport_cores import TRANSPORT_CORES

__author__ = "Ivan de Paz Centeno"
import logging
from pyvirtualdisplay import Display
from selenium.webdriver import Firefox
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from time import sleep, time

TIMEOUT = 5


class WebCore(object):
    """
    Represents the transport core for the surface web.
    """

    def __init__(self, gui=True, window_size=(1280, 1000)):
        try:
            self.gui = gui
            profile = webdriver.FirefoxProfile()
            profile.set_preference("browser.cache.disk.enable", False)
            profile.set_preference("browser.cache.memory.enable", False)
            profile.set_preference("browser.cache.offline.enable", False)
            profile.set_preference("network.http.use-cache", False)

            if not gui:
                self.virtual_browser_display = Display(visible=0, size=(800, 600))
                self.virtual_browser_display.start()

            self.virtual_browser = Firefox(profile)
            self.virtual_browser.set_window_size(*window_size)
        except Exception as ex:
            logging.info("Error: {}".format(ex))
        #self.virtual_browser.set_window_position(-1000, -1000)

    def get(self, url):
        logging.debug("Get started")
        self.virtual_browser.get(url)
        logging.debug("Get finished")

    def get_elements_html_by_class(self, class_name, innerHTML=True):
        if innerHTML:
            attribute = 'innerHTML'
        else:
            attribute = 'outerHTML'

        logging.debug("Getting elements by class {}".format(class_name))

        elements_by_class =[]

        try:
            elements_by_class = self.virtual_browser.find_elements_by_class_name(class_name)
            logging.debug("Retrieved {} elements of class {}".format(len(elements_by_class), class_name))
        except Exception as ex:
            logging.debug("Error while retrieving the elements by class {}: {}".format(len(elements_by_class),
                                                                                      class_name))

        result = [element.get_attribute(attribute) for element in elements_by_class]
        print("[WEBCORE] result len is {}".format(len(result)))
        return result

    def get_elements_html_by_tag(self, tag_name, innerHTML=True):
        if innerHTML:
            attribute = 'innerHTML'
        else:
            attribute = 'outerHTML'

        return [element.get_attribute(attribute) for element in
                self.virtual_browser.find_elements_by_tag_name(tag_name)]

    def get_elements_html_by_id(self, id, innerHTML=True):
        if innerHTML:
            attribute = 'innerHTML'
        else:
            attribute = 'outerHTML'

        return [element.get_attribute(attribute) for element in
                self.virtual_browser.find_elements_by_id(id)]

    def scroll_to_bottom(self):
        self.virtual_browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        logging.info("Scrolling to the bottom")
        sleep(0.2)

    def __del__(self):
        self.virtual_browser.close()

        if self.gui:
            self.virtual_browser_display.stop()

    def send_text_to_input_by_id(self, param, text):
        input_box = self.virtual_browser.find_element_by_id(param)
        input_box.send_keys(text)

    def click_button_by_class(self, param):
        try:
            button = self.virtual_browser.find_element_by_class_name(param)
        except Exception as ex:
            logging.info("Error: {}".format(ex))
            button= None

        if button:
            button.click()

    def wait_for_elements_from_class(self, class_name):
        sleep(0.5)
        WebDriverWait(self.virtual_browser, 5).until(EC.presence_of_element_located((By.CLASS_NAME, class_name)))

    def manual_wait_for_element_from_class(self, class_name):
        """
        Waits for the element by manually polling the amoung of elements of the given class in the DOM, for a timeout
        of 5 seconds.
        :param class_name:
        :return:
        """
        init_time = time()

        while len(self.get_elements_html_by_class(class_name)) == 0 and time() - init_time < TIMEOUT:
            sleep(1)

# Register the class to enable deserialization.
TRANSPORT_CORES[str(WebCore)] = WebCore
