#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import logging
import os

import zmq

__author__ = 'Iván de Paz Centeno'


class ServiceClient(object):
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.context = zmq.Context()
        self.is_connected = False

    def __connect__(self):
        self.worker = self.context.socket(zmq.DEALER)
        self.worker.setsockopt_string(zmq.IDENTITY, str(os.getpid()))
        self.worker.connect("tcp://{}:{}".format(self.host, self.port))
        self.is_connected = True

    def __disconnect__(self):
        self.worker.close()
        self.is_connected = False

    def __send_request__(self, formatted_request):
        try:
            if not self.is_connected:
                self.__connect__()

            self.worker.send_json(formatted_request)
        except:
            logging.info("Could not send the request to the remote endpoint ({}:{}).".format(self.host, self.port))
            self.is_connected = False

    def __get_response__(self):
        response = {}

        try:
            if self.is_connected:
                response = self.worker.recv_json()
                self.__disconnect__()
            else:
                logging.info("Endpoint not connected and can't receive ({}:{}).".format(self.host, self.port))

        except:
            logging.info("Could not receive the request's response the remote endpoint ({}:{}).".format(self.host,
                                                                                                        self.port))
            self.is_connected = False

        return response
