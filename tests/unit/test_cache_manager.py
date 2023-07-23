#!/usr/bin/env python3
import os
import shutil
import pytest
import tempfile
from yaht.cache_management import CacheManager, CacheIndex


@pytest.fixture
def cache_dir():
    new_dir = tempfile.mkdtemp()
    yield os.path.join(new_dir, "cache")
    shutil.rmtree(new_dir)


def test_cache_creation(cache_dir):
    """Test that a new cache creates a folder and has a CacheIndex"""
    cache = CacheManager(cache_dir)
    assert os.path.exists(cache_dir)
    cache_index = cache.cache_index
    assert type(cache_index) is CacheIndex


def test_send_data(cache_dir):
    """Test that we can call send_data with the right arguments"""
    # The data must have a descriptor, and the actual data
    test_data = {"legend": "Some descriptor", "data": "Some test data"}
    data_hash = "someKey"

    # Send the data
    cache = CacheManager(cache_dir)
    cache.send_data(data_hash, test_data)

    # Check that a file is created
    cache_index = cache.cache_index
    expected_file = cache_index.get_item_filename(data_hash)
    assert os.path.exists(expected_file)


def test_get_data(cache_dir):
    """Test getting a value back from the cache"""
    test_data = {"legend": "Some descriptor", "data": "Some test data"}
    data_hash = "someKey"
    cache = CacheManager(cache_dir)
    cache.send_data(data_hash, test_data)

    # Attempt to retrieve the data and check it's the same
    retrieved_data = cache.get_data(data_hash)
    assert retrieved_data == test_data


def test_delete_data(cache_dir):
    """Test deleting a value from the cache"""
    # Send some data to the cache
    test_data = {"legend": "Some descriptor", "data": "Some test data"}
    data_hash = "someKey"
    cache = CacheManager(cache_dir)
    cache.send_data(data_hash, test_data)

    # Record what the filename of the test data would be
    cache_index = cache.cache_index
    filename = cache_index.get_item_filename(data_hash)

    # Delete the data and check that the file and entry no longer exist
    cache.delete_data(data_hash)
    assert not cache_index.check_item_exists(data_hash)
    assert not os.path.exists(filename)


def test_check_cache(cache_dir):
    """
    Test that we can check whether a hash exists in the cache
    without loading the relevant data
    """
    # Send some data to the cache
    test_data = {"legend": "Some descriptor", "data": "Some test data"}
    data_hash = "someKey"
    cache = CacheManager(cache_dir)
    cache.send_data(data_hash, test_data)

    # Check that it exists
    assert cache.check_data(data_hash) == True

    # Delete the data and check that it no longer exists
    cache.delete_data(data_hash)
    assert cache.check_data(data_hash) == False
