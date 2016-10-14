#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import logging
from time import sleep

from main.dataset.data_fetcher import DataFetcher
from main.dataset.dataset import Dataset
import os

__author__ = "Ivan de Paz Centeno"

DEFAULT_METADATA_FILE_NAME="metadata.json"


class GenericDataset(Dataset):

    def __init__(self, name, search_session, root_folder=None):
        if not root_folder:
            root_folder = "/tmp/{}_dataset/".format(name)

        self.name = name
        metadata_file = os.path.join(root_folder, DEFAULT_METADATA_FILE_NAME)

        Dataset.__init__(self, root_folder, metadata_file, "Generic dataset")

        self.search_session = search_session
        self.data_fetcher = DataFetcher(self.root_folder)
        self.data_fetcher.start()

    def fetch_data(self, wait_for_finish=True):
        """
        Fetchs the crawled data from the search_session.
        The fetched content are stored internally, and can be used to build a metadata for the current dataset.

        :param wait_for_finish: waits until all the crawled data from search session is fetched.
                Warning: if the search_session crawlers haven't finished yet it might be possible for this fetcher
                to finish before all the data is crawled. This may happen if the fetch process is faster than the
                crawling one. Thus, you should invoke this method multiple times depending on the state of
                search_session if you want to do both tasks in parallel.
        :return:
        """
        logging.info("Fetching data...")
        data_fetcher = self.data_fetcher

        history = self.search_session.get_history()

        result_sets = [history[search_request_key].get_result() for search_request_key in history]

        logging.info("Retrieved {} result sets".format(len(result_sets)))

        [data_fetcher.fetch_requests(result_set) for result_set in result_sets]

        while wait_for_finish and data_fetcher.get_percent_done() < 100 and len(result_sets) > 0:
            logging.info("Progress: {}%".format(data_fetcher.get_percent_done()))

            sleep(1)

        logging.info("Data fetched.")

    def get_percent_fetched(self):
        return self.data_fetcher.get_percent_done()

    def build_metadata(self, save_to_file=True):
        """
        Builds the metadata file with the retrieved dataset content.
        If the save_to_file flag is set, the file is saved in the DEFAULT_METADATA_FILE_NAME (metadata.json) under the
        root_folder defined during construction.
        :param save_to_file: flag to indicate if the metadata content must be saved to a file or not.
        :return:
        """

        try:
            results_json = self.data_fetcher.get_results()
            self.metadata_content = {
                'name': self.name,
                'description': self.description,
                'data': results_json
            }

            logging.info("Metadata built successfully: {}".format(self.metadata_content))

            if save_to_file:
                uri = self.metadata_file

                directory = os.path.dirname(uri)
                if not os.path.exists(directory):
                    os.makedirs(directory)

                with open(uri, "w") as file:
                    json.dump(self.metadata_content, file, indent=4, sort_keys=True)

                logging.info("Dataset metadata saved to file {}".format(uri))
        except Exception as ex:
            logging.info("Could not build the metadata. Reason: {}".format(str(ex)))

    def __del__(self):
        self.data_fetcher.stop()