#!/usr/bin/env python3
import os
import shutil
import pytest
import tempfile
import datetime
import numpy as np
import pandas as pd
import yaht.cache_management as CM


@pytest.fixture
def cache_dir():
    new_dir = tempfile.mkdtemp()
    yield os.path.join(new_dir, "cache")
    shutil.rmtree(new_dir)


def test_store_data(cache_dir):
    """Test saving some data to the cache"""
    fake_data = ["This", "is", "some", "fake", "data"]
    data_hash = "DATA_KEY"
    CM.store_cache_data(cache_dir, data_hash, fake_data)
    # There should be some metadata in the cache now
    metadata = CM.load_cache_metadata(cache_dir).set_index("hash")
    relevant_metadata = metadata.loc["DATA_KEY"]
    assert relevant_metadata.any()


def test_load_data(cache_dir):
    """Test retrieving data by data hash"""
    fake_data = ["This", "is", "some", "fake", "data"]
    data_hash = "DATA_KEY"
    CM.store_cache_data(cache_dir, data_hash, fake_data)
    # We should then be able to retrieve the data by key
    loaded_data = CM.load_cache_data(cache_dir, data_hash)
    assert loaded_data == fake_data


def test_data_creation_date(cache_dir):
    """Test that we record the date some data was created as metadata"""
    fake_data = ["This", "is", "some", "fake", "data"]
    data_hash = "DATA_KEY"
    # Record the current time and save the data
    save_time = datetime.datetime.now()
    CM.store_cache_data(cache_dir, data_hash, fake_data)
    # There should be some metadata in the cache now
    metadata = CM.load_cache_metadata(cache_dir).set_index("hash")
    recorded_save_time = metadata.loc["DATA_KEY", "time_created"]
    assert recorded_save_time >= save_time
    assert recorded_save_time <= save_time + datetime.timedelta(seconds=1)


def test_data_last_changed_date(cache_dir):
    """Test that the last time some data was changed is stored"""
    fake_data = ["This", "is", "some", "fake", "data"]
    data_hash = "DATA_KEY"
    CM.store_cache_data(cache_dir, data_hash, fake_data)
    # The save time should be the same as the update time
    metadata = CM.load_cache_metadata(cache_dir).set_index("hash")
    recorded_time_created = metadata.loc[data_hash, "time_created"]
    recorded_time_modified = metadata.loc[data_hash, "time_modified"]
    assert recorded_time_created == recorded_time_modified

    # If we then store some other data to override the original data
    new_fake_data = ["This", "is", "some", "new", "fake", "data"]
    CM.store_cache_data(cache_dir, data_hash, new_fake_data)
    # the update time should change
    metadata = CM.load_cache_metadata(cache_dir).set_index("hash")
    recorded_time_created = metadata.loc[data_hash, "time_created"]
    recorded_time_modified = metadata.loc[data_hash, "time_modified"]
    assert recorded_time_created < recorded_time_modified
