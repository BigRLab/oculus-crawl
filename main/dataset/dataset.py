#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'Iván de Paz Centeno'

import fnmatch
import os


class Dataset(object):

    def __init__(self, root_folder, metadata_file, description):
        self.root_folder = root_folder
        self.metadata_file = metadata_file
        self.description = description
        self.default_extension = '.jpg'
        self.metadata_content = []
        self.routes = []

    def __load_routes__(self):
        for root, dirnames, filenames in os.walk(self.root_folder):
            for filename in fnmatch.filter(filenames, "*" + self.default_extension):
                self.routes.append(os.path.join(root, filename))

    def __load_metadata_file__(self):
        with open(self.metadata_file) as file:
            self.metadata_content = filter(None, file.readlines())

    def get_root_folder(self):
        return self.root_folder

    def get_metadata_file(self):
        return self.metadata_file

    def get_description(self):
        return self.description

    # each class must override this method since the key to search
    # could be different in each case.
    # def find_image_route(self, image_id):

    def get_metadata_content(self):
        return self.metadata_content
