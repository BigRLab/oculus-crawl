#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import os

import io
from PIL import Image

__author__ = "Ivan de Paz Centeno"


class MemDatabase(object):

    def __init__(self, to_folder):
        self.data = {}
        self.urls = []
        self.result_data = {}
        self.number_count = {}
        self.in_progress = {}
        self.to_folder = to_folder

    def append(self, url, metadata):
        self.data[url] = metadata
        self.urls.append(url)

    def get_value(self, url):
        return self.data[url]

    def pop_url(self):

        if len(self.urls) > 0:
            url = self.urls.pop()
            self.in_progress[url] = True
        else:
            url = None

        return url

    def add_result_data(self, url, image_bytes, extension):

        # We cache the images by their hash
        image_hash = url  # get_image_hash(image_bytes)
        metadata = self.get_value(url)
        metadata['extension'] = extension

        if not image_bytes:
            del self.in_progress[url]
            return

        if image_hash in self.result_data:

            # We found the same image but probably with different URL.
            if url not in self.result_data[image_hash]['metadata']['url']:
                self.result_data[image_hash]['metadata']['url'].append(url)

            if url not in self.result_data[image_hash]['metadata']['source']:
                self.result_data[image_hash]['metadata']['source'].append(metadata['source'])

            self.result_data[image_hash]['metadata']['desc'] += metadata['desc']
            logging.info("Adding to existing url {}".format(url))
        else:
            uri = self._generate_uri(metadata)
            self.result_data[image_hash]= {'metadata' : metadata}
            self.result_data[image_hash]['metadata']['url'] = [url]
            self.result_data[image_hash]['metadata']['source'] = [metadata['source']]

            self._save_image_bytes(image_bytes, uri)
            logging.info("Saved url {} in {}".format(url, uri))

            self.result_data[image_hash]['metadata']['uri'] = [uri]

        del self.in_progress[url]

    def _generate_uri(self, metadata):

        if metadata['source'] not in self.number_count:
            self.number_count[metadata['source']] = 0

        number = self.number_count[metadata['source']]

        self.number_count[metadata['source']] += 1

        return "{}{}".format(os.path.join(self.to_folder, metadata['source'], str(number)), metadata['extension'])

    def get_percent_done(self):
        if len(self.urls) + len(self.in_progress) + len(self.result_data)== 0:
            result = 0
        else:
            result = int(len(self.result_data) / (len(self.urls) + len(self.in_progress) + len(self.result_data)) * 100)

        return result

    @staticmethod
    def _save_image_bytes(image_bytes, uri):

        #image = Image.open(io.BytesIO(image_bytes))
        directory = os.path.dirname(uri)
        if not os.path.exists(directory):
            os.makedirs(directory)

        with open(uri, "wb") as file:
            file.write(image_bytes)
        #image.save(uri)

    def get_result_data(self):
        return self.result_data