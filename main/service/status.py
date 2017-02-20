#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
from datetime import datetime
from multiprocessing import Lock

import multiprocessing

__author__ = "Ivan de Paz Centeno"


# **********************************
# SERVICE GENERIC STATUS
# **********************************
# You can define more service status flags:
SERVICE_RUNNING = 0
# ----
# All the flags behind 0 are considered as service running.
# Example:
# SERVICE_FETCHING_DATA = -1

SERVICE_STOPPED = 1
# ----
# All the flags above 1 are considered as service stopped.
# Example:
# SERVICE_CRASH = 2


# **********************************
# SERVICE DATASET BUILDER STATUS
# **********************************
SERVICE_CRAWLING_DATA = -1
SERVICE_FETCHING_DATA = -2
SERVICE_FILTERING_DATA = -3
SERVICE_COMPRESSING_DATA = -4
SERVICE_PUBLISHING_DATA = -5
SERVICE_CREATED_DATASET = 2
SERVICE_STATUS_UNKNOWN = 9999

CODE_MAP = {
    SERVICE_RUNNING: "SERVICE_RUNNING",
    SERVICE_STOPPED: "SERVICE_STOPPED",

    SERVICE_CRAWLING_DATA: "SERVICE_CRAWLING_DATA",
    SERVICE_FETCHING_DATA: "SERVICE_FETCHING_DATA",
    SERVICE_FILTERING_DATA: "SERVICE_FILTERING_DATA",
    SERVICE_COMPRESSING_DATA: "SERVICE_COMPRESSING_DATA",
    SERVICE_PUBLISHING_DATA: "SERVICE_PUBLISHING_DATA",
    SERVICE_CREATED_DATASET: "SERVICE_CREATED_DATASET",

    SERVICE_STATUS_UNKNOWN: "SERVICE_STATUS_UNKNOWN",
}

CODE_MAP_INV = {v: k for k, v in CODE_MAP.items()}


def get_status_name(status_code):

    if status_code in CODE_MAP:
        result = CODE_MAP[status_code]
    else:
        result = "SERVICE_STATUS_UNKNOWN"

    return result


def get_status_by_name(status_code_name):

    if status_code_name in CODE_MAP_INV:
        result = CODE_MAP_INV[status_code_name]
    else:
        result = SERVICE_STATUS_UNKNOWN

    return result


class GlobalStatus(object):
    """
    Allows tracking status of each spawned process
    """

    def __init__(self, manager):
        self.global_lock = Lock()
        self.status_table = manager.dict()
        self.manager = manager

    def update_proc_progress(self, header, current, max=100):
        """
        Updates the text for the caller process with a progress bar.
        :param header:
        :param current:
        :param min:
        :param max:
        :return:
        """
        self.update_proc("{} :: [{}%] {} ".format(self._create_progress_representation(current, max),
                                                  round(current / max * 100, 2),
                                                  header))

    @staticmethod
    def _create_progress_representation(current, max, max_chars=20):
        result = "["

        threshold = (max_chars * current) / max

        for index in range(max_chars):

            if index < threshold:
                result += "#"
            else:
                result += "-"

        result += "]"

        return result

    def update_proc(self, string_status):
        """
        Adds a register for PID caller to this method with the string status.
        :param string_status: any string representative for the status of the process.
        """

        pid = os.getpid()

        with self.global_lock:
            now = datetime.now()
            self.status_table[pid] = {
                "time": now,
                "status": string_status
            }

    def get_manager(self):
        return self.manager

    def __str__(self):
        """
        String representation of the global status.
        :return:
        """
        with self.global_lock:
            status_table = dict(self.status_table)

        result = ""

        for pid in list(set(status_table)):
            status_value = status_table[pid]
            result += "[{} - {}] - {}\n".format(pid, status_value["time"], status_value["status"])

        return result



manager = multiprocessing.Manager()
status = GlobalStatus(manager)