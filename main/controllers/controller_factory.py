#!/usr/bin/env python
# -*- coding: utf-8 -*-
from main.controllers.dataset_factory_controller import DatasetFactoryController
from main.controllers.search_session_controller import SearchSessionController

__author__ = "Ivan de Paz Centeno"


CONTROLLERS_LIST = {
    'dataset_factory_controller': DatasetFactoryController,
    'search_session_controller': SearchSessionController,
}


class ControllerFactory(object):
    """
    Factory for controllers.
    Eases the creation of controllers by injecting common dependencies, like the services definition
    and the app handler.
    """

    def __init__(self, flask_app, dataset_factory):
        """
        Initializes the factory with minimum parameters.
        :param flask_app: application of Flask to handle the requests.
        """
        self.flask_app = flask_app

        self.dataset_factory = dataset_factory

        self.controllers = {}

        # This dict acts like the global CONTROLLERS_LIST, but
        # proxying the instantation with the factory method.
        # This is specially useful for ensemble controllers that depends
        # on atomic controllers.
        self.controllers_creation_method = {
            'search_session_controller': self.search_session_controller,
            'dataset_factory_controller': self.dataset_factory_controller,
        }

    def search_session_controller(self):
        """
        Singleton-creation of the search_session controller.
        When this method is invoked, it will add the controller for the search session to the flask app.
        If the controller already exists, it will only return a reference to it.
        :return: the controller that handles the search sessions.
        """
        controller_name = 'search_session_controller'

        if controller_name not in self.controllers:
            self.controllers[controller_name] = self._create_atomic_controller(controller_name)

        return self.controllers[controller_name]

    def dataset_factory_controller(self):
        """
        Singleton-creation of the dataset factory controller.
        When this method is invoked, it will add the controller for the dataset factory to the flask app.
        If the controller already exists, it will only return a reference to it.
        :return: the controller that handles the search sessions.
        """
        controller_name = 'dataset_factory_controller'

        if controller_name not in self.controllers:
            self.controllers[controller_name] = self._create_atomic_controller(controller_name)

        return self.controllers[controller_name]

    def _create_atomic_controller(self, controller_name):
        """
        Generates a controller for the given name (available controllers' names at global CONTROLLERS_LIST var.

        :param controller_name: The name of the controller to create
        :param services_type: Type of the services to inject to the controller.
        :param services_subtype: Subtype of the services to inject to the controller.
        :return: The created controller instance. If the name of the controller does not exist, it will raise an
        exception.
        """

        # The available services for this controller should be a reduced set of services.
        # Reason: it makes no sense to have a feet detection controller with face algorithms.

        if controller_name not in CONTROLLERS_LIST:
            raise Exception("Controller name does not exist.")

        return CONTROLLERS_LIST[controller_name](flask_web_app=self.flask_app, dataset_factory=self.dataset_factory)
