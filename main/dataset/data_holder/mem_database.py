#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import os

import io
from PIL import Image
import hashlib

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

        if url in self.data:
            self.data[url].append(metadata)
        else:
            self.data[url] = [metadata]

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

        if not image_bytes:
            del self.in_progress[url]
            return

        # We cache the images by their hash
        image_hash = self._get_image_hash(image_bytes) # get_image_hash(image_bytes)
        metadatas = self.get_value(url)  # we may have multiple metadata for a single URL

        for metadata_element in metadatas:
            if 'extension' not in metadata_element:
                metadata_element['extension'] = extension


        if image_hash not in self.result_data:
            [absolute_uri, relative_uri] = self._generate_uri(metadatas[0])
            self.result_data[image_hash]= {'metadata': metadatas[0].copy()}

            self.result_data[image_hash]['metadata']['url'] = []
            self.result_data[image_hash]['metadata']['source'] = []
            self.result_data[image_hash]['metadata']['searchwords'] = []
            self.result_data[image_hash]['metadata']['desc'] = ""
            self.result_data[image_hash]['metadata']['uri'] = [relative_uri]

            self._save_image_bytes(image_bytes, absolute_uri)
            logging.debug("Saved url {} in {}".format(url, absolute_uri))

        url_was_inside = True
        if url not in self.result_data[image_hash]['metadata']['url']:
            self.result_data[image_hash]['metadata']['url'].append(url)
            url_was_inside = False

        for metadata in metadatas:
            if metadata['source'] not in self.result_data[image_hash]['metadata']['source']:
                self.result_data[image_hash]['metadata']['source'].append(metadata['source'])

            if metadata['desc'] not in self.result_data[image_hash]['metadata']['desc'] and not url_was_inside:
                # Let's remove previous search-words

                self.result_data[image_hash]['metadata']['desc'] += metadata['desc'] + ";"

            if metadata['searchwords'] not in self.result_data[image_hash]['metadata']['searchwords']:
                self.result_data[image_hash]['metadata']['searchwords'].append(metadata['searchwords'])

        del self.in_progress[url]

    @staticmethod
    def _get_image_hash(image_bytes):
        """
        Computes the image hash from its array of bytes
        :param self:
        :param image_bytes: array of bytes of the image (it is not a numpy array, it is the image in binary format,
        like jpg or png).
        :return:
        """
        return hashlib.md5(image_bytes).hexdigest()

    def _generate_uri(self, metadata):
        """
        Generates the URI to the downloaded resource.
        :param metadata: data retrieved from a search_request processed by a search_engine
        :return: [absolute URI, relative URI]
        """
        if metadata['source'] not in self.number_count:
            self.number_count[metadata['source']] = 0

        number = self.number_count[metadata['source']]

        self.number_count[metadata['source']] += 1

        return ["{}{}".format(os.path.join(self.to_folder, metadata['source'], str(number)), metadata['extension']),
                "{}{}".format(os.path.join(metadata['source'], str(number)), metadata['extension'])]

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