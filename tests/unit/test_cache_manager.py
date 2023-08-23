#!/usr/bin/env python3
import os
import pickle
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
    data_hash = "someKey"
    test_data = "someTestData"
    metadata = {"source": "someSource"}

    # Send the data
    cache = CacheManager(cache_dir)
    cache.send_data(data_hash, test_data)  # On its own
    cache.send_data(data_hash, test_data, metadata)  # With metadata

    # Check that a file is created
    assert len(os.listdir(cache_dir)) > 0


def test_get_data(cache_dir):
    """Test getting a value back from the cache"""
    data_hash = "someKey"
    test_data = "someTestData"
    cache = CacheManager(cache_dir)
    cache.send_data(data_hash, test_data)

    # Attempt to retrieve the data and check it's the same
    retrieved_data = cache.get_data(data_hash)
    assert retrieved_data == test_data


def test_get_metadata(cache_dir):
    """Test that we can retrieve metadata after it's been saved"""
    data_hash = "someKey"
    test_data = "someTestData"
    metadata = {"source": "someSource"}

    # Send the data
    cache = CacheManager(cache_dir)
    cache.send_data(data_hash, test_data, metadata)

    # And retrieve it again
    source = cache.get_metadata(data_hash, "source")
    assert source == "someSource"


def test_get_key_by_metadata(cache_dir):
    """Test that we can get a list of keys associated with a given metadata"""
    data_hash = "someKey"
    test_data = "someTestData"
    metadata = {"source": "someSource"}

    # Send the data
    cache = CacheManager(cache_dir)
    cache.send_data(data_hash, test_data, metadata)

    # And retrieve the key
    keys = cache.get_keys_by_metadata("someSource", "source")
    assert keys == ["someKey"]


def test_delete_data(cache_dir):
    """Test deleting a value from the cache"""
    # Send some data to the cache
    data_hash = "someKey"
    test_data = "someTestData"
    cache = CacheManager(cache_dir)
    cache.send_data(data_hash, test_data)

    # Record what the filename of the test data would be
    cache_index = cache.cache_index
    filename = cache_index.get_item_metadata(data_hash, "filename")

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
    data_hash = "someKey"
    test_data = "someTestData"
    cache = CacheManager(cache_dir)
    cache.send_data(data_hash, test_data)

    # Check that it exists
    assert cache.check_data(data_hash) == True

    # Delete the data and check that it no longer exists
    cache.delete_data(data_hash)
    assert cache.check_data(data_hash) == False


def test_add_file(cache_dir):
    """Test adding an existing file of data to the cache"""
    # Create some fake data in a different fake folder
    fake_dir = tempfile.mkdtemp()
    data_fname = os.path.join(fake_dir, "mock_data.pickle")
    data = "mockData"
    with open(data_fname, "wb") as f:
        pickle.dump(data, f)

    cache = CacheManager(cache_dir)
    cache.add_file(data_fname)

    # Check that the file now exists in the cache
    expected_cached_file = os.path.join(cache_dir, "mock_data.pickle")
    assert os.path.exists(expected_cached_file)
    # Attempt to retrieve the data by filename
    data_key = cache.get_keys_by_metadata("mock_data.pickle", "filename")[0]
    retrieved_data = cache.get_data(data_key)
    assert retrieved_data == data
