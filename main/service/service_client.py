#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import logging
import os

import time
import zmq
from multiprocessing import Lock

__author__ = 'Iván de Paz Centeno'


class ServiceClient(object):
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.context = zmq.Context()
        self.lock = Lock()

    def get_host(self):
        return self.host

    def get_port(self):
        return self.port

    def _connect(self):
        self.worker = self.context.socket(zmq.DEALER)
        self.worker.setsockopt_string(zmq.IDENTITY, str(time.time()))
        self.worker.connect("tcp://{}:{}".format(self.host, self.port))
        logging.debug("Connected.")

    def _disconnect(self):
        logging.debug("Disconnected.")
        self.worker.close()

    def _send_request(self, formatted_request):
        response = {}
        abort = False

        with self.lock:
            try:
                self._connect()
                self.worker.send_json(formatted_request)

            except Exception as ex:
                logging.info("Could not send the request to the remote endpoint ({}:{}). Reason: {}".format(self.host,
                                                                                                            self.port,
                                                                                                            ex))
                self._disconnect()
                abort = True

            try:
                if abort:
                    raise Exception("Won't wait for a response when the request couldn't be sent.")
                response = self.worker.recv_json()
                self._disconnect()

            except Exception as ex:
                logging.info("Could not receive the response from the remote endpoint ({}:{}). Reason: {}".format(
                                                                                                            self.host,
                                                                                                            self.port,
                                                                                                            ex))
                self._disconnect()

        return response
