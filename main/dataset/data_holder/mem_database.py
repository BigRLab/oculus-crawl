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

        # We cache the images by their hash
        image_hash = url  # get_image_hash(image_bytes)
        metadatas = self.get_value(url)  # we may have multiple metadata for a single URL

        for metadata_element in metadatas:
            if 'extension' not in metadata_element:
                metadata_element['extension'] = extension

        if not image_bytes:
            del self.in_progress[url]
            return

        if image_hash in self.result_data:
            # We found the same image but probably with different URL or different metadata.
            url_already_cached = url in self.result_data[image_hash]['metadata']['url']

            if not url_already_cached:
                self.result_data[image_hash]['metadata']['url'].append(url)
                # Same image, Different URL
                for metadata in metadatas:
                    if metadata['source'] not in self.result_data[image_hash]['metadata']['source']:
                        # Same image, Different URL, Different Search-Engine
                        self.result_data[image_hash]['metadata']['source'].append(metadata['source'])
                    #else:
                        # Same image, Different URL, Same Search-Engine

                    if metadata['desc'] not in self.result_data[image_hash]['metadata']['desc']:
                        self.result_data[image_hash]['metadata']['desc'] += metadata['desc']

            else:
                # Same image, Same URL,
                for metadata in metadatas:
                    if metadata['source'] not in self.result_data[image_hash]['metadata']['source']:
                        # Same image, Same URL, Different Search-Engine
                        self.result_data[image_hash]['metadata']['source'].append(metadata['source'])
                        self.result_data[image_hash]['metadata']['desc'] += metadata['desc']

                    if metadata['desc'] not in self.result_data[image_hash]['metadata']['desc']:
                        self.result_data[image_hash]['metadata']['desc'] += metadata['desc']

            logging.debug("Adding to existing image hash")

        else:
            [absolute_uri, relative_uri] = self._generate_uri(metadatas[0])
            self.result_data[image_hash]= {'metadata' : metadatas[0]}

            self.result_data[image_hash]['metadata']['url'] = [url]
            self.result_data[image_hash]['metadata']['source'] = [metadatas[0]['source']]

            for metadata in metadatas:
                if metadata['source'] not in self.result_data[image_hash]['metadata']['source']:
                    # Same image, Same URL, Different Search-Engine
                    self.result_data[image_hash]['metadata']['source'].append(metadata['source'])
                    self.result_data[image_hash]['metadata']['desc'] += metadata['desc']

            self._save_image_bytes(image_bytes, absolute_uri)
            logging.debug("Saved url {} in {}".format(url, absolute_uri))

            self.result_data[image_hash]['metadata']['uri'] = [relative_uri]

        del self.in_progress[url]

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