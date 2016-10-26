#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging

from main.dataset.dataset import DATASET_TYPES
from main.dataset.dataset_builder import DatasetBuilder
from main.dataset.generic_dataset import GenericDataset
from main.search_session.search_session import SearchSession
from main.service.service import Service, SERVICE_STOPPED
from main.service.socket_interface import SocketInterface
from main.service.status import get_status_name, SERVICE_CRAWLING_DATA, SERVICE_FETCHING_DATA, SERVICE_FILTERING_DATA, \
    SERVICE_RUNNING

__author__ = "Ivan de Paz Centeno"


class DatasetFactory(Service, SocketInterface):
    """
    Represents a center for datasets, which can be accessed to add new dataset requests or check the status of the
    builds.

    It is Factory and a service, publishing some RPC through a TCP port.
    """

    def __init__(self, host="0.0.0.0", port=24005, autostart=True, zmq_context=None):
        Service.__init__(self)
        SocketInterface.__init__(self, host, port, zmq_context)

        with self.lock:
            self.datasets_builders_working = {}

        self.used_ports = []
        self.port_range = [24010, 24500]

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

    '''
    def get_dataset_builder_list(self):
        """
        Retrieves the datasets builders in progress.
        If a dataset builder is not in the list, it is sure that the dataset builder has already finished and its
        results published.
        :return:
        """

        return [self.datasets_builders_working[key] for key in self.datasets_builders_working]
    '''

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
                percent_done_set = [*self.datasets_builders_working[name].get_percent_done()]
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

    '''
    def remove_dataset_builder(self, dataset_builder):
        """
        Removes the dataset_builder from the list
        :param dataset_builder:
        :return:
        """
        if dataset_builder.get_dataset_name() in self.datasets_builders_working:
            del self.datasets_builders_working[dataset_builder.get_dataset_name()]
    '''

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

    def create_dataset(self, name, host="0.0.0.0", port=None, dataset_type=GenericDataset):
        """
        Creates a new dataset builder and a search_session associated to it.
        The search session is created with the parameters
        By default, the dataset builder is stopped until at least one search request is appended.

        :param host: host for the search session. Crawlers will seek for this session's search requests on this host.
        :param port: port for the search session. Crawlers will seek for this session's search requests on this port.
        :return: True if datasetbuilder created, false otherwise. Consider using this as a True/False boolean if you
        want to keep compatibility with the remote_dataset_factory implementation.
        """

        if not port:
            new_port = self._allocate_new_port()
        else:
            new_port = port

        with self.lock:
            name_taken = name in self.datasets_builders_working

        if new_port and not name_taken:
            with self.lock:
                search_session = SearchSession(host=host, port=new_port, zmq_context=self.get_context())
                self.used_ports.append(new_port)
                dataset_builder = DatasetBuilder(search_session, name, autostart=True, dataset_type=dataset_type,
                                                 autoclose_search_session_on_exit=True,
                                                 on_finished=self._on_builder_finished)
                logging.info("Started dataset builder for {}".format(name))
                self.datasets_builders_working[name] = dataset_builder

        else:
            dataset_builder = None

        return dataset_builder

    def __internal_thread__(self):
        Service.__internal_thread__(self)
        SocketInterface.init_socket(self)

        while not self.__get_stop_flag__():

            [request, identity, exit_requested] = self.get_new_request()

            if exit_requested:

                self.__set_stop_flag__()

            elif 'action' in request:

                # logging.info(request)

                {
                    'create_dataset': self._create_dataset,
                    'get_dataset_names_list': self._get_dataset_names_list,
                    'get_dataset_progress_by_name': self._get_dataset_progress_by_name,
                    'remove_dataset_by_name': self._remove_dataset_by_name,
                    'get_session_by_dataset_name': self._get_session,
                    'get_sessions_from_datasets': self._get_sessions_list,
                }[request['action']](identity, request)

        SocketInterface.terminate(self)

        with self.lock:
            dataset_builders = [dataset_builder for name, dataset_builder in self.datasets_builders_working.items()]
            self.datasets_builders_working.clear()

        for dataset_builder in dataset_builders:
            logging.info("Stopping dataset builder...")
            dataset_builder.stop()
            logging.info("Stopped.")

        self.__set_status__(SERVICE_STOPPED)

    def _create_dataset(self, identity, request):
        """
        Creates a new dataset in the list.
        :param self:
        :param identity:
        :param request:
        :return:
        """
        host = "0.0.0.0"
        port = None

        try:

            assert 'name' in request and request['name']

            if 'dataset_type' in request:
                if request['dataset_type'] not in DATASET_TYPES:
                    raise Exception("The specified type of dataset is not valid.")

                if 'host' in request:
                    host = request['host']

                if 'port' in request:
                    port = request['port']
                else:
                    port = None

                dataset_type = DATASET_TYPES[request['dataset_type']]

            else:
                dataset_type = GenericDataset

            logging.info("Creating dataset with name {}".format(request['name']))
            if self.create_dataset(request['name'], host=host, port=port, dataset_type=dataset_type):
                logging.info("Dataset with name {} initialized".format(request['name']))
                result = {'result': 'Done'}
            else:
                logging.error("Dataset name {} is already taken".format(request['name']))
                result = {'error': 'dataset name already taken'}

        except Exception as ex:

            result = {'error': 'Request malformed ({}).'.format(ex)}

        SocketInterface.send_response(self, identity, result)

    def _get_dataset_names_list(self, identity, request):
        """
        Creates a session and returns the IP and Port of it.
        :param self:
        :param identity:
        :param request:
        :return:
        """
        with self.lock:
            result = {'result': [name for name in self.datasets_builders_working]}

        SocketInterface.send_response(self, identity, result)

    def _allocate_new_port(self):
        """
        Allocates a new port from the range defined in port_range
        :param self:
        :return: the first port available or None otherwise
        """
        for port in range(*self.port_range):
            if port not in self.used_ports:
                return port

        return None

    def _get_session(self, identity, request):
        """
        Returns a session host-port pair by the given name.
        :return:
        """
        result = {}

        try:
            if 'name' not in request:
                raise Exception("A dataset name must be provided")

            name = request['name']

            with self.lock:
                if name not in self.datasets_builders_working:
                    raise Exception("Dataset name not available")

                session = self.datasets_builders_working[name].get_search_session()

                result = {'result': {'host': session.get_host(), 'port': session.get_port()}}

        except Exception as ex:
            result['error'] = str(ex)

        SocketInterface.send_response(self, identity, result)

    def _remove_dataset_by_name(self, identity, request):
        """
        Called whenever a dataset is wanted to be removed.
        :param identity:
        :param request:
        :return:
        """
        result = {}

        try:
            if 'name' not in request:
                raise Exception("A name must be provided")

            if request['name'] not in self.datasets_builders_working:
                raise Exception("Name is not in the available list.")

            self.remove_dataset_builder_by_name(request['name'])

            result = {'result': 'Done'}

        except Exception as ex:
            result['error'] = str(ex)

        SocketInterface.send_response(self, identity, result)

    def _get_dataset_progress_by_name(self, identity, request):
        """
        Called whenever the progress of the dataset is requested.
        :param identity:
        :param request:
        :return:
        """
        result = {}

        try:
            if 'name' not in request:
                raise Exception("A name must be provided")

            with self.lock:

                if request['name'] not in self.datasets_builders_working:
                    raise Exception("Name is not in the working datasets builders list.")

            percent_done = self.get_dataset_builder_percent(request['name'])

            result['result'] = percent_done

        except Exception as ex:
            result['error'] = str(ex)

        SocketInterface.send_response(self, identity, result)

    def _get_sessions_list(self, identity, request):
        """
        Called whenever the sessions are required.
        :param identity:
        :param request:
        :return:
        """

        with self.lock:

            result = {'result': [{'name': name,
                                  'host': dataset_builder.get_search_session().get_host(),
                                  'port': dataset_builder.get_search_session().get_port()}
                                 for name, dataset_builder in self.datasets_builders_working.items()]}

        SocketInterface.send_response(self, identity, result)

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

        # Lets free the port from the used ports, as it is released from now on
        with self.lock:
            self.used_ports.remove(dataset_session.get_port())

        if dataset_session.get_status() != SERVICE_STOPPED:
            dataset_session.stop()