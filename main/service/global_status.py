#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
from datetime import datetime
from multiprocessing import Lock
from main.service.service import Service

import multiprocessing

__author__ = 'Iván de Paz Centeno'


class GlobalStatus(Service):
    """
    Allows tracking status of each spawned process
    """

    def __init__(self, manager):
        Service.__init__(self)

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

    #def get_manager(self):
    #    return self.manager

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

    def __internal_thread__(self):
        """
        Internal backgrounded code. Prints the current status of the crawler and its threads.

        :return: None
        """

        lines_handled = 1

        try:
            while not self.__get_stop_flag__():
                status_string = str(self)
                lines_count = len(status_string.split("\n")) + 1

                lines_to_add = max(1, lines_count-lines_handled)
                lines_handled = lines_count
                print("\n"*lines_to_add, end="")

                status_string = "{}{}".format("\033[F" * lines_handled, status_string)
                print(status_string)
                time.sleep(0.5)
        except:
            pass

        return None


manager = multiprocessing.Manager()
global_status = GlobalStatus(manager)
global_status.start()
