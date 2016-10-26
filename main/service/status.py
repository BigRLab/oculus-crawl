#!/usr/bin/env python
# -*- coding: utf-8 -*-

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
