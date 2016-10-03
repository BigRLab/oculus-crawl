#!/usr/bin/env python
# -*- coding: utf-8 -*-
from main.dataset.dataset import Dataset
import os

__author__ = "Ivan de Paz Centeno"

DEFAULT_METADATA_FILE_NAME="metadata.json"


class GenericDataset(Dataset):

    def __init__(self, name, search_session, root_folder=None):
        if not root_folder:
            root_folder = "/tmp/{}_dataset/".format(name)

        metadata_file = os.path.join(root_folder, DEFAULT_METADATA_FILE_NAME)

        Dataset.__init__(self, root_folder, metadata_file, "Generic dataset")

        self.search_session =