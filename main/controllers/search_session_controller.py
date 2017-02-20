#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import jsonify
from flask import request

from main.controllers.controller import route, Controller
from main.exceptions.invalid_request import InvalidRequest
from main.search_session.search_request import SearchRequest


__author__ = "Ivan de Paz Centeno"


class SearchSessionController(Controller):
    """
    Controller for /dataset/<dataset_name>/session/ URL
    """

    def __init__(self, flask_web_app, dataset_factory):
        """
        Constructor of the Session Controller.
        :param flask_web_app: web app from Flask already initialized.
        :param dataset_factory: factory of datasets to manipulate.
        """
        Controller.__init__(self, flask_web_app, dataset_factory)

        self.exposed_methods += [
            self.append_search_requests,
            self.reset_search_request,
            self.size,
            self.pop_request,
            self.add_to_history,
            self.get_completion_progress,
            self.get_session_data,
            self.set_session_data,
            self.get_history,
        ]

        self._init_exposed_methods()

    @route("/dataset/<dataset_name>/session/size", methods=['GET'])
    def size(self, dataset_name):
        """
        Retrieves the size of the session from the dataset_name
        :return:
        """
        session = self.dataset_factory.get_session_from_dataset_name(dataset_name)

        if session is None:
            raise InvalidRequest("Dataset does not exist.", status_code=401)

        return str(session.size())

    @route("/dataset/<dataset_name>/session/search-request", methods=['GET'])
    def pop_request(self, dataset_name):
        """
        Retrieves a request from the specified dataset name.
        :param dataset_name:
        :return: search_request
        """

        session = self.dataset_factory.get_session_from_dataset_name(dataset_name)

        if session is None:
            raise InvalidRequest("Dataset does not exist.", status_code=401)

        new_request = session.pop_new_search_request()

        if new_request:
            new_request = new_request.serialize()
        else:
            raise InvalidRequest("No requests available for the session.", status_code=404)

        return jsonify(new_request)

    @route("/dataset/<dataset_name>/session/search-request", methods=['PUT'])
    def append_search_requests(self, dataset_name):
        """
        Puts search requests into the session of the specified dataset builder.
        :return:
        """

        session = self.dataset_factory.get_session_from_dataset_name(dataset_name)

        if session is None:
            raise InvalidRequest("Dataset does not exist.", status_code=401)

        resquest_json = request.get_json()

        if 'search_request' in resquest_json:
            resquest_json['search_requests'] = [resquest_json['search_requests']]

        elif 'search_requests' not in resquest_json:
            raise InvalidRequest("No search requests provided to append.")

        search_requests = [SearchRequest.deserialize(search_request) for search_request in resquest_json['search_requests']]

        session.append_search_requests(search_requests)

        return ""

    @route("/dataset/<dataset_name>/session/search-request", methods=['PATCH'])
    def reset_search_request(self, dataset_name):
        """
        Resets search requests of the specified session.
        :return:
        """

        session = self.dataset_factory.get_session_from_dataset_name(dataset_name)

        if session is None:
            raise InvalidRequest("Dataset does not exist.", status_code=401)

        request_json = request.get_json()

        if 'search_request' not in request_json:
            raise InvalidRequest("No search request provided to reset.")

        search_request = SearchRequest.deserialize(request_json['search_request'])

        session.reset_search_request(search_request)

        return ""

    @route("/dataset/<dataset_name>/session/completion-progress", methods=['GET'])
    def get_completion_progress(self, dataset_name):
        """
        Retrieves the completion progress for the session from the dataset_name
        :return:
        """
        session = self.dataset_factory.get_session_from_dataset_name(dataset_name)

        if session is None:
            raise InvalidRequest("Dataset does not exist.", status_code=401)

        return str(session.get_completion_progress())

    @route("/dataset/<dataset_name>/session/data", methods=['GET'])
    def get_session_data(self, dataset_name):
        """
        Retrieves the data of the session from the dataset_name
        :return:
        """
        session = self.dataset_factory.get_session_from_dataset_name(dataset_name)

        if session is None:
            raise InvalidRequest("Dataset does not exist.", status_code=401)

        request = self._get_validated_request()

        if 'dump_in_progress_as_pending' not in request:
            dump_in_progress_as_pending = True
        else:
            dump_in_progress_as_pending = request['dump_in_progress_as_pending']

        return jsonify({'result': session.serialize(dump_in_progress_as_pending=dump_in_progress_as_pending)})

    @route("/dataset/<dataset_name>/session/data", methods=['PUT'])
    def set_session_data(self, dataset_name):
        """
        Sets the data of the session for the dataset_name
        :return:
        """
        session = self.dataset_factory.get_session_from_dataset_name(dataset_name)

        if session is None:
            raise InvalidRequest("Dataset does not exist.", status_code=401)

        request_args = self._get_validated_request()

        if 'load_in_progress_as_pending' not in request_args:
            raise InvalidRequest("Boolean flag load_in_progress_as_pending missing in the request.")

        resquest_json = request.get_json()

        if 'data' not in resquest_json:
            raise InvalidRequest("Data missing in the request content.")

        load_in_progress_as_pending = request_args['load_in_progress_as_pending']
        data = resquest_json['data']

        try:
            session.deserialize(data, dump_in_progress_as_pending=load_in_progress_as_pending)

        except Exception as ex:
            raise InvalidRequest("Session could not deserialize the data. It seems to be malformed.", 500)

        return ""

    @route("/dataset/<dataset_name>/session/history", methods=['GET'])
    def get_history(self, dataset_name):
        """
        Retrieves the history of the session from the dataset_name
        :return:
        """
        session = self.dataset_factory.get_session_from_dataset_name(dataset_name)

        if session is None:
            raise InvalidRequest("Dataset does not exist.", status_code=401)

        session_history = session.get_search_history()

        return jsonify({'result':[session_history[search_request_hash].serialize() for search_request_hash in
                                  session_history]})

    @route("/dataset/<dataset_name>/session/history", methods=['PUT'])
    def add_to_history(self, dataset_name):
        """
        Puts search requests into the history of the session from the specified dataset builder.
        :return:
        """

        session = self.dataset_factory.get_session_from_dataset_name(dataset_name)

        if session is None:
            raise InvalidRequest("Dataset does not exist.", status_code=401)

        resquest_json = request.get_json()

        if 'search_request' not in resquest_json:
            raise InvalidRequest("No search request provided for history.")

        search_request = SearchRequest.deserialize(resquest_json['search_request'])

        session.add_history_entry(search_request)

        return ""