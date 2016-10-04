#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import os

__author__ = "Ivan de Paz Centeno"


class MemDatabase(object):

    def __init__(self, to_folder):
        self.data = {}
        self.urls = []
        self.result_data = {}
        self.number_count = {}
        self.to_folder = to_folder

    def append(self, url, metadata):
        self.data[url] = metadata
        self.urls.append(url)

    def get_value(self, url):
        return self.data[url]

    def pop_url(self):

        if len(self.urls) > 0:
            url = self.urls.pop()
        else:
            url = None

        return url

    def add_result_data(self, url, image_bytes):

        logging.info("Adding url {}".format(url))
        # We cache the images by their hash
        image_hash = url  # get_image_hash(image_bytes)
        metadata = self.get_value(url)

        if image_hash in self.result_data:

            # We found the same image but probably with different URL.
            if url not in self.result_data[image_hash]['metadata']['url']:
                self.result_data[image_hash]['metadata']['url'].append(url)

            if url not in self.result_data[image_hash]['metadata']['source']:
                self.result_data[image_hash]['metadata']['source'].append(metadata['source'])

            self.result_data[image_hash]['metadata']['desc'] += metadata['desc']
            logging.info("Adding to existing url {}".format(url))
        else:
            logging.info("Hi")
            uri = self._generate_uri(metadata)
            self.result_data[image_hash]= {'metadata' : metadata}
            logging.info("Ho")
            self.result_data[image_hash]['metadata']['url'] = [url]
            logging.info("Hu")
            self.result_data[image_hash]['metadata']['source'] = [metadata['source']]

            logging.info("Saving url {}".format(url))
            self._save_image_bytes(image_bytes, uri)
            logging.info("Saved url {} in {}".format(url, uri))

            self.result_data[image_hash]['metadata']['uri'] = [uri]

    def _generate_uri(self, metadata):

        if metadata['source'] not in self.number_count:
            self.number_count[metadata['source']] = 0

        number = self.number_count[metadata['source']]

        self.number_count[metadata['source']] += 1

        return "{}.jpg".format(os.path.join(self.to_folder, metadata['source'], str(number)))

    @staticmethod
    def _save_image_bytes(image_bytes, uri):

        with open(uri, "wb") as file:
            file.write(image_bytes)