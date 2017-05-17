#!/usr/bin/env python
# -*- coding: utf-8 -*-

from functools import partial
from multiprocessing import Lock
from flask import jsonify, request
from main.exceptions.invalid_request import InvalidRequest


__author__ = "Ivan de Paz Centeno"


def route(*args, **kwargs):
    """
    Decorator proxy for @self.flask_web_app.route.
    Since we cannot use "self" while calling the decorator, proxying it is a good solution.
    :param args:
    :param kwargs:
    :return:
    """
    def decorator1(func):

        def decorator2(self):

            app = self.flask_web_app
            # At this level we have the app defined, extracted from self.

            partial_func = partial(func, self)
            app.add_url_rule(*(args + ("{}.{}".format(self.__class__.__name__, func.__name__), partial_func)), **kwargs)

        return decorator2

    return decorator1


def error_handler(*args, **kwargs):
    """
    Decorator proxy for @self.flask_web_app.errorhandler.

    Since we cannot use "self" while calling the decorator, proxying it is a good solution.
    :param args:
    :param kwargs:
    :return:
    """

    def decorator1(func):
        def decorator2(self):
            app = self.flask_web_app

            # At this level we have the app defined, extracted from self.

            partial_func = partial(func, self)

            app.register_error_handler(*(args, partial_func))

        return decorator2

    return decorator1


class Controller(object):
    """
    Generic controller super class.
    Inherit it to build a controller.
    """

    def __init__(self, flask_web_app, dataset_factory):
        """
        Constructor of the controller.
        :param flask_web_app: flask app object.
        :param dataset_factory:  factory for datasets to manipulate.
        :param options:  set of options specified as program arguments.
        """
        self.lock = Lock()
        self.flask_web_app = flask_web_app
        self.dataset_factory = dataset_factory

        self.exposed_methods = [
            self.handle_invalid_request
        ]

    def _init_exposed_methods(self):
        """
        Initializes the exposed methods to be API-REST callable.
        """
        [exposed_method() for exposed_method in self.exposed_methods]

    @staticmethod
    def _get_validated_request(should_have_uri=False):
        """
        Validates the request to fit a basic protocol. If the request does not fit the protocol, it will raise
        an exception.
        Override this method to change or extend the default validation of the incoming request.

        :param should_have_uri: flag to specify if the request should contain an URI or not.
        :return: the request validated.
        """

        request_args = request.args

        if should_have_uri and request_args.get("uri", '') == '':
            raise InvalidRequest("Request URI is missing.")

        return request_args

    @error_handler(InvalidRequest)
    def handle_invalid_request(self, error):
        """
        Handles the invalid request error in order to formally notify the appropriate code.
        :param error: dict containing the explanation of the error.
        :return:
        """
        response = jsonify(error.to_dict())
        response.status_code = error.status_code
        return response

    def release_services(self, wait_for_close=True):
        """
        Releases the controller's services
        """
        pass

    def __del__(self):
        """
        On destruction of the object, all the services are released.
        """

        self.release_services()
