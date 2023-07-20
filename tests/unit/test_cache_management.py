#!/usr/bin/env python3
import os
import pytest
import shutil
import tempfile
from yaht.cache_management import CacheManager


@pytest.fixture
def cache_dir():
    new_dir = tempfile.mkdtemp()
    yield os.path.join(new_dir, "cache")
    shutil.rmtree(new_dir)


def test_cache_creation(cache_dir):
    """Test that if we initialize a cache, the relevant folder is created"""
    cache = CacheManager(cache_dir)
    assert os.path.exists(cache_dir)


def test_get_set_data(cache_dir):
    """Test pushing a value to the cache"""
    # The data must have a descriptor, and the actual data
    test_data = {"descriptor": "Some descriptor", "data": "Some test data"}
    data_hash = "someKey"

    # Send the data
    cache = CacheManager(cache_dir)
    cache.send_data(data_hash, test_data)

    # Then try to retrieve it
    retrieved_data = cache.get_data(data_hash)

    assert retrieved_data == test_data


# def test_get_deleted_data():
#     """Test retrieving a value from the cache"""
#     # Send some data to the cache, and then try to retrieve it
#     data_dir = ""
#     pass


# def test_check_cache():
#     """
#     Test that we can check whether a hash exists in the cache
#     without loading the relevant data
#     """
#     # Send some data to the cache

#     #


# def test_clear_cache():
#     """Test that we can clear a created cache without deleting the cache structure"""
#     # Create a cache and send some data to it

#     # Delete the cache and check that the relevant folders still exist


# def test_clear_cache_conditional():
#     """Should be able to clear e.g. parts of cache not accessed in X time"""
#     pass


# def test_cache_visibility():
#     pass
