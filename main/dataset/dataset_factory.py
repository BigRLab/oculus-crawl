#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging

from main.dataset.dataset_builder import DatasetBuilder
from main.dataset.generic_dataset import GenericDataset
from main.search_session.search_session import SearchSession
from main.service.service import Service, SERVICE_STOPPED
from main.service.status import get_status_name, SERVICE_CRAWLING_DATA, SERVICE_FETCHING_DATA, \
    SERVICE_RUNNING

__author__ = "Ivan de Paz Centeno"


class DatasetFactory(Service):
    """
    Represents a center for datasets, which can be accessed to add new dataset requests or check the status of the
    builds.

    It is Factory and a service, publishing some RPC through a TCP port.
    """

    def __init__(self, autostart=True, publish_dir="/tmp/"):
        Service.__init__(self)

        self.publish_dir = publish_dir

        with self.lock:
            self.datasets_builders_working = {}

        if autostart:
            self.start()

    def get_dataset_builders_sessions(self):
        with self.lock:
            result = [self.datasets_builders_working[dataset_builder_name].get_search_session() for dataset_builder_name
                      in self.datasets_builders_working]

        return result

    def get_session_from_dataset_name(self, name):

        with self.lock:

            if name in self.datasets_builders_working:
                search_session = self.datasets_builders_working[name].get_search_session()
            else:
                search_session = None

        return search_session

    def get_dataset_builder_percent(self, name):
        """
        Returns the percent done for the specified dataset name in a dict.
        {
         'percent': percent
         'status': "status_text"
        }

        Check the available status for the dataset builder in service/status.py

        :param name: dataset name whose percent is desired.
        :return: percent of completion of the dataset
        """

        with self.lock:
            if name in self.datasets_builders_working:
                percent_crawled, percent_fetched = self.datasets_builders_working[name].get_percent_done()
                percent_done_set = [percent_crawled, percent_fetched]
                status = self.datasets_builders_working[name].get_status()

                percent_status_map = {
                    SERVICE_RUNNING: 0,
                    SERVICE_CRAWLING_DATA: percent_done_set[0],
                    SERVICE_FETCHING_DATA: percent_done_set[1],
                    #SERVICE_FILTERING_DATA: percent_done[2]
                }

                if status in percent_status_map:
                    percent_done = percent_status_map[status]
                else:
                    percent_done = -1

                result = {'percent': percent_done, 'status': get_status_name(status)}
            else:
                result = {'status': 'UNKNOWN'}

        return result

    def get_dataset_builder_names(self):
        """
        Returns a list of names of the dataset builders in progress.
        :return:
        """
        with self.lock:
            result = [key for key in self.datasets_builders_working]

        return result

    def remove_dataset_builder_by_name(self, name):
        """
        Removes the dataset_builder from the list
        :param name: name of the dataset to remove from the list
        :return:
        """
        with self.lock:
            if name in self.datasets_builders_working:
                self.datasets_builders_working[name].stop(False)
                del self.datasets_builders_working[name]

    def create_dataset(self, name, dataset_type=GenericDataset):
        """
        Creates a new dataset builder and a search_session associated to it.
        The search session is created with the parameters
        By default, the dataset builder is stopped until at least one search request is appended.

        :return: True if datasetbuilder created, false otherwise. Consider using this as a True/False boolean if you
        want to keep compatibility with the remote_dataset_factory implementation.
        """

        with self.lock:
            name_taken = name in self.datasets_builders_working

        if not name_taken:
            with self.lock:
                search_session = SearchSession()
                dataset_builder = DatasetBuilder(search_session, name, autostart=True, dataset_type=dataset_type,
                                                 autoclose_search_session_on_exit=True, publish_dir=self.publish_dir,
                                                 on_finished=self._on_builder_finished)
                logging.info("Started dataset builder for {}".format(name))
                self.datasets_builders_working[name] = dataset_builder

        else:
            dataset_builder = None

        return dataset_builder

    def _on_builder_finished(self, name):
        """
        This method is called whenever a dataset builder finished its job.
        We need to remove the dataset builder from the working list since its session is
        freed, and can make freezes on crawlers when they try to find the progress of the available sessions.

        :param name: name of the dataset builder to remove from the list.
        :return:
        """
        dataset_session = self.get_session_from_dataset_name(name)
        self.remove_dataset_builder_by_name(name)

        if dataset_session and dataset_session.get_status() != SERVICE_STOPPED:
            dataset_session.stop()


