#!/usr/bin/env python3
import os
import pickle
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


def test_generate_cache_metadata(cache_dir):
    """
    The cache metadata should be a dataframe
    relating hashes to filenames and other metadata
    """
    metadata = CM.load_cache_metadata(cache_dir)

    # With no cache to start with, should load a df with a single empty row
    assert type(metadata) == pd.DataFrame
    assert len(metadata) == 0
    # Calling load_cache_metadata should create a cache folder and a metadata file
    metadata_path = os.path.join(cache_dir, "metadata.csv")
    assert os.path.exists(metadata_path)


def test_store_metadata(cache_dir):
    """We should be able to store to the metadata by providing rows of data"""
    # Saving should work even if cache_dir doesn't exist
    new_metadata = pd.DataFrame(
        [
            {
                "hash": "SOME_HASH",
                "filename": "some_filename",
                "sources": ["some_source"],
            },
            {
                "hash": "ANOTHER_HASH",
                "filename": "another_filename",
                "sources": ["another_source"],
            },
        ]
    )
    CM.store_cache_metadata(cache_dir, new_metadata)

    # We should then be able to load the metadata
    loaded_metadata = CM.load_cache_metadata(cache_dir).set_index("hash")
    assert loaded_metadata.loc["SOME_HASH", "filename"] == "some_filename"
    assert loaded_metadata.loc["SOME_HASH", "sources"] == ["some_source"]
    assert loaded_metadata.loc["ANOTHER_HASH", "filename"] == "another_filename"
    assert loaded_metadata.loc["ANOTHER_HASH", "sources"] == ["another_source"]


def test_default_values(cache_dir):
    """
    Check the datatypes of columns in the metadata
    as well as the default 'empty' values
    """
    empty_metadata = CM.load_cache_metadata(cache_dir)

    # Check dtypes where relevant
    metadata_dtypes = empty_metadata.dtypes
    assert pd.api.types.is_string_dtype(metadata_dtypes["hash"])
    assert pd.api.types.is_string_dtype(metadata_dtypes["filename"])
    assert pd.api.types.is_object_dtype(metadata_dtypes["sources"])  # Lists
    assert pd.api.types.is_datetime64_any_dtype(metadata_dtypes["time_created"])
    assert pd.api.types.is_datetime64_any_dtype(metadata_dtypes["time_modified"])

    new_metadata = pd.DataFrame([{"hash": "SOME_HASH"}])
    CM.store_cache_metadata(cache_dir, new_metadata)
    loaded_metadata = CM.load_cache_metadata(cache_dir)

    # Check dtypes are consistent after saving and loading
    metadata_dtypes = loaded_metadata.dtypes
    assert pd.api.types.is_string_dtype(metadata_dtypes["hash"])
    assert pd.api.types.is_string_dtype(metadata_dtypes["filename"])
    assert pd.api.types.is_object_dtype(metadata_dtypes["sources"])  # Lists
    assert pd.api.types.is_datetime64_any_dtype(metadata_dtypes["time_created"])
    assert pd.api.types.is_datetime64_any_dtype(metadata_dtypes["time_modified"])

    # Check the empty / default values
    loaded_metadata = loaded_metadata.set_index("hash")
    assert loaded_metadata.loc["SOME_HASH", "filename"] == "SOME_HASH"
    assert loaded_metadata.loc["SOME_HASH", "sources"] == []
    assert loaded_metadata.loc["SOME_HASH", "time_created"] < datetime.datetime.now()
    assert (
        loaded_metadata.loc["SOME_HASH", "time_modified"]
        == loaded_metadata.loc["SOME_HASH", "time_created"]
    )


def test_override_metadata(cache_dir):
    """Test overriding existing metadata by hash key"""
    new_metadata = pd.DataFrame(
        [
            {
                "hash": "SOME_HASH",
                "filename": None,
                "sources": ["some_source"],
            },
            {
                "hash": "ANOTHER_HASH",
                "filename": "another_filename",
                "sources": [],
            },
        ]
    )
    CM.store_cache_metadata(cache_dir, new_metadata)

    # Now store the same data but with different values missing etc
    new_metadata = pd.DataFrame(
        [
            {
                "hash": "SOME_HASH",
                "filename": "some_filename",
                "sources": [],
            },
            {
                "hash": "ANOTHER_HASH",
                "filename": "OVERRIDE_filename",
                "sources": [],
            },
        ]
    )
    CM.store_cache_metadata(cache_dir, new_metadata)

    # Loading the data should then load us the combined data
    loaded_metadata = CM.load_cache_metadata(cache_dir).set_index("hash")
    assert len(loaded_metadata) == 2
    assert loaded_metadata.loc["SOME_HASH", "filename"] == "some_filename"
    assert loaded_metadata.loc["SOME_HASH", "sources"] == ["some_source"]
    assert loaded_metadata.loc["ANOTHER_HASH", "filename"] == "OVERRIDE_filename"
    assert loaded_metadata.loc["ANOTHER_HASH", "sources"] == []


def test_metadata_column_stability(cache_dir):
    """Test that adding metadata over and over doesn't created or destroy new columns"""
    new_metadata = pd.DataFrame(
        [
            {
                "hash": "SOME_HASH",
                "filename": None,
                "sources": ["some_source"],
            },
            {
                "hash": "ANOTHER_HASH",
                "filename": "another_filename",
                "sources": [],
            },
        ]
    )
    CM.store_cache_metadata(cache_dir, new_metadata)
    original_stored_metadata = CM.load_cache_metadata(cache_dir)

    # Now store the same data but with different values missing etc
    new_metadata = pd.DataFrame(
        [
            {
                "hash": "SOME_HASH",
                "filename": "some_filename",
                "sources": [],
            },
            {
                "hash": "ANOTHER_HASH",
                "filename": "OVERRIDE_filename",
                "sources": [],
            },
        ]
    )
    CM.store_cache_metadata(cache_dir, new_metadata)
    new_stored_metadata = CM.load_cache_metadata(cache_dir)

    assert (original_stored_metadata.columns == new_stored_metadata.columns).all()


def test_multiple_sources(cache_dir):
    """
    Test that passing different sources for one hash
    Stores all of them in a list
    """
    # One hash, two sources
    new_metadata = pd.DataFrame(
        [
            {
                "hash": "SOME_HASH",
                "sources": ["first_source", "second_source"],
            },
        ]
    )
    CM.store_cache_metadata(cache_dir, new_metadata)

    loaded_metadata = CM.load_cache_metadata(cache_dir).set_index("hash")
    # There should be a single item with both sources listed
    assert len(loaded_metadata) == 1
    expected_sources = ["first_source", "second_source"]
    assert loaded_metadata.loc["SOME_HASH", "sources"] == expected_sources

    # We should them be able to add another source in the same way
    new_metadata = pd.DataFrame(
        [
            {
                "hash": "SOME_HASH",
                "sources": ["third_source"],
            }
        ]
    )
    CM.store_cache_metadata(cache_dir, new_metadata)

    loaded_metadata = CM.load_cache_metadata(cache_dir).set_index("hash")
    # There should still be a single item, with all sources listed
    assert len(loaded_metadata) == 1
    expected_sources = ["first_source", "second_source", "third_source"]
    assert set(loaded_metadata.loc["SOME_HASH", "sources"]) == set(expected_sources)


def test_modified_filenames(cache_dir):
    """Test that we can update filenames to be based on data sources"""
    fake_data = ["This", "is", "some", "fake", "data"]
    data_hash = "DATA_KEY"
    CM.store_cache_data(cache_dir, data_hash, fake_data)
    # Get the original filename for reference
    old_metadata = CM.load_cache_metadata(cache_dir).set_index("hash")
    old_filename = old_metadata.loc[data_hash, "filename"]

    # Test that running the function without changing metadata doesn't change the filename
    CM.update_cache_filenames(cache_dir)
    still_old_metadata = CM.load_cache_metadata(cache_dir).set_index("hash")
    still_old_filename = still_old_metadata.loc[data_hash, "filename"]
    assert still_old_filename == old_filename

    # If we now add a data source to the metadata and update the filenames..
    new_metadata = pd.DataFrame(
        {
            "hash": [data_hash],
            "sources": [["some-MaDe*uP/Source"]],
        }
    )
    # Filename should be all lowercase, with special chars converted to underscores
    # plus a fragment of the hash to prevent collisions
    expected_filename = "some_made_up_source_DATA"
    CM.store_cache_metadata(cache_dir, new_metadata)
    CM.update_cache_filenames(cache_dir)
    # Check new filenames
    metadata = CM.load_cache_metadata(cache_dir).set_index("hash")
    filename = metadata.loc[data_hash, "filename"]
    assert filename == expected_filename
    assert os.path.exists(os.path.join(cache_dir, filename))
    # Check the old file is gone
    assert not os.path.exists(os.path.join(cache_dir, old_filename))

    # TODO: Test that the first source is used for the filename?


def test_sync_cache_metadata(cache_dir):
    """
    Test that by deleting or adding files in the cache
    we delete or add their metadata as well
    """
    CM.store_cache_data(cache_dir, "fake_key", "fake_data")
    # First add a file and see if it syncs with the metadata
    with open(os.path.join(cache_dir, "NEW_FILE"), "wb") as f:
        pickle.dump("some_new_data", f)
    # The cache should only update after the function is called
    assert len(CM.load_cache_metadata(cache_dir)) == 1
    save_time = datetime.datetime.now()
    CM.sync_cache_metadata(cache_dir)
    # The created hash should be the same as the filename
    assert CM.load_cache_data(cache_dir, "NEW_FILE") == "some_new_data"
    synced_metadata = CM.load_cache_metadata(cache_dir).set_index("hash")
    assert len(synced_metadata) == 2
    # And the time it was synced should also be saved
    recorded_save_time = synced_metadata.loc["NEW_FILE", "time_created"]
    assert recorded_save_time >= save_time
    assert recorded_save_time <= save_time + datetime.timedelta(seconds=1)
    assert recorded_save_time == synced_metadata.loc["NEW_FILE", "time_modified"]

    # Then delete the file and check it no longer exists in the metadata
    os.remove(os.path.join(cache_dir, "NEW_FILE"))
    CM.sync_cache_metadata(cache_dir)
    assert len(CM.load_cache_metadata(cache_dir)) == 1
