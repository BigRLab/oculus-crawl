#!/usr/bin/env python
# -*- coding: utf-8 -*-
from main.dataset.remote_dataset_factory import RemoteDatasetFactory
from main.search_engine import yahoo_images, bing_images, flickr_images, google_images, howold_images
import sys

__author__ = "Ivan de Paz Centeno"


remote_dataset_factory = RemoteDatasetFactory("http://localhost:24005/")

dataset_names = remote_dataset_factory.get_dataset_builder_names()

if len(dataset_names) == 0:
    remote_dataset_factory.create_dataset("test")

dataset_names = remote_dataset_factory.get_dataset_builder_names()
dataset_name = dataset_names[0]

session = remote_dataset_factory.get_session_from_dataset_name(dataset_name)

print("size:", session.size())
while session.pop_new_search_request() is not None:
    print(".",end="")
    sys.stdout.flush()

print("size:", session.size())

session.load_session("Backup_snapshot_test.json")
print("Backup loaded.")

#session.save_session("Backup_snapshot_test.json")
#print("Backup saved.")