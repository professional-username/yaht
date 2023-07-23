#!/usr/bin/env python3
import os
import pytest
import tempfile
from yaht.cache_management import CacheIndex

INDEX_FNAME = "cacheIndex"


@pytest.fixture
def cache_dir():
    new_dir = tempfile.mkdtemp()
    yield os.path.join(new_dir, "cache")


def test_create_cache_index(cache_dir):
    """Test that initializing a CacheIndex creates an index file in the cache"""
    CacheIndex(cache_dir)
    expected_index_path = os.path.join(cache_dir, INDEX_FNAME)
    assert os.path.exists(expected_index_path)


# NOTE: Maybe unnecessary
# def test_sqlite_db_structure(cache_dir):
#     """Test that the cache created is an SQLite database with the correct structure"""
#     CacheIndex(cache_dir)
#     index_path = os.path.join(cache_dir, INDEX_FNAME)
#     # Connect to SQLite database
#     connection = sqlite3.connect(cache_dir)
#     cursor = connection.cursor()
#     # Query and check the tables in the db


def test_create_item(cache_dir):
    """Test that we can add an item to the index"""
    index = CacheIndex(cache_dir)
    # Add an item, only specifying the key
    index.add_item("someHashKey")
    # Add an item, specifying a key and legend
    index.add_item("anotherHashKey", legend="someLegend")


def test_get_item_file(cache_dir):
    """Test that after creating an item we can retrieve its file"""
    index = CacheIndex(cache_dir)
    # Add an item and try to get its file
    hash_key = "someHashKey"
    index.add_item(hash_key)
    file = index.get_item_filename(hash_key)
    assert file is not None


def test_get_item_legend(cache_dir):
    """Test that after creating an item we can retrieve its legend"""
    index = CacheIndex(cache_dir)
    # Add an item, specifying a key and legend
    index.add_item("someHashKey", legend="someLegend")
    legend = index.get_item_legend("someHashKey")
    assert legend == "someLegend"


# TODO
# def test_get_item_creation_time(cache_dir):
#     """Test getting the datetime that the item was created at"""

# TODO
# def test_get_item_last_accessed_time(cache_dir):
#     """Test getting the datetime that the item was last accessed at"""
