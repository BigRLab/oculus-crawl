#!/usr/bin/env python
# -*- coding: utf-8 -*-
import time

from main.search_session.remote_search_session import RemoteSearchSession
from main.search_session.search_session import SearchSession
from main.service.service import Service, SERVICE_STOPPED
from main.service.socket_interface import SocketInterface

__author__ = "Ivan de Paz Centeno"


class DatasetFactory(Service, SocketInterface):
    """
    Represents a center for datasets, which can be accessed to add new dataset requests or check the status of the
    builds.

    It is Factory.
    """

    def __init__(self, host="0.0.0.0", port=24005, autostart=True):
        Service.__init__(self)
        SocketInterface.__init__(self, host, port)

        self.search_sessions = []
        self.used_ports = []
        self.port_range = [24010, 24500]

        if autostart:
            self.start()

    def get_sessions(self):
        """
        Retrieves the sessions stored in this session center.
        :return:
        """
        return self.search_sessions

    def remove_session(self, session):
        """
        Removes the session from the list
        :param session:
        :return:
        """
        if session in self.search_sessions:
            self.search_sessions.remove(session)

    def create_session(self, host="0.0.0.0", port=None):
        """
        Creates a new session for search requests.
        :param host:
        :param port:
        :return:
        """
        search_session = None

        if port:
            new_port = self._allocate_new_port()
        else:
            new_port = port

        if new_port:
            search_session = SearchSession(host=host, port=new_port)
            self.used_ports.append(new_port)

        return search_session

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
                    'create_session': self._create_session,
                    'add_session': self._add_session,
                    'get_session_by_index': self._get_session,
                    'list_sessions': self._list_sessions,
                    'remove_session_by_index': self._remove_session,
                }[request['action']](identity, request)

        SocketInterface.terminate(self)

        self.__set_status__(SERVICE_STOPPED)

    def _add_session(self, identity, request):
        """
        Add session a session to the current session list.
        :param self:
        :param identity:
        :param request:
        :return:
        """
        try:
            assert 'ip' in request
            assert 'port' in request

        except Exception as ex:
            result = {'error': 'Request malformed.'}

        ip = request['ip']
        port = request['port']
        self.search_sessions.append(RemoteSearchSession(ip, port))

        SocketInterface.send_response(self, identity, {'result': True})

    def _create_session(self, identity, request):
        """
        Creates a session and returns the IP and Port of it.
        :param self:
        :param identity:
        :param request:
        :return:
        """
        result = {}

        if 'host' in request:
            host = request['host']
        else:
            host = "0.0.0.0"

        result['host'] = host

        new_port = self._allocate_new_port()

        if new_port:
            search_session = SearchSession(host=host, port=new_port)
            self.used_ports.append(new_port)
            result['port'] = new_port
        else:
            result['error'] = "No ports available for new sessions."

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
        Returns a session host-port pair by the given index.
        :return:
        """
        result = {}

        try:
            if 'id' not in request:
                raise Exception("Index value missing")

            request_id = request['id']
            if request_id >= len(self.search_sessions):
                raise Exception("Index out of bounds.")

            session = self.search_sessions[request_id]

            result = {'host': session.get_host(), 'port': session.get_port()}

        except Exception as ex:
            result['error'] = str(ex)

        SocketInterface.send_response(self, identity, result)