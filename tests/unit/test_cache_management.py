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
                "source": "some_source",
            },
            {
                "hash": "ANOTHER_HASH",
                "filename": "another_filename",
                "source": "another_source",
            },
        ]
    )
    CM.store_cache_metadata(cache_dir, new_metadata)

    # We should then be able to load the metadata
    loaded_metadata = CM.load_cache_metadata(cache_dir).set_index("hash")
    assert loaded_metadata.loc["SOME_HASH", "filename"] == "some_filename"
    assert loaded_metadata.loc["SOME_HASH", "source"] == "some_source"
    assert loaded_metadata.loc["ANOTHER_HASH", "filename"] == "another_filename"
    assert loaded_metadata.loc["ANOTHER_HASH", "source"] == "another_source"


def test_override_metadata(cache_dir):
    """Test overriding existing metadata by hash key"""
    new_metadata = pd.DataFrame(
        [
            {
                "hash": "SOME_HASH",
                "filename": None,
                "source": "some_source",
            },
            {
                "hash": "ANOTHER_HASH",
                "filename": "another_filename",
                "source": np.nan,
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
                "source": np.nan,
            },
            {
                "hash": "ANOTHER_HASH",
                "filename": "OVERRIDE_filename",
                "source": None,
            },
        ]
    )
    CM.store_cache_metadata(cache_dir, new_metadata)

    # Loading the data should then load us the combined data
    loaded_metadata = CM.load_cache_metadata(cache_dir).set_index("hash")
    assert len(loaded_metadata) == 2
    assert loaded_metadata.loc["SOME_HASH", "filename"] == "some_filename"
    assert loaded_metadata.loc["SOME_HASH", "source"] == "some_source"
    assert loaded_metadata.loc["ANOTHER_HASH", "filename"] == "OVERRIDE_filename"
    assert np.isnan(loaded_metadata.loc["ANOTHER_HASH", "source"])


def test_metadata_column_stability(cache_dir):
    """Test that adding metadata over and over doesn't created or destroy new columns"""
    new_metadata = pd.DataFrame(
        [
            {
                "hash": "SOME_HASH",
                "filename": None,
                "source": "some_source",
            },
            {
                "hash": "ANOTHER_HASH",
                "filename": "another_filename",
                "source": np.nan,
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
                "source": np.nan,
            },
            {
                "hash": "ANOTHER_HASH",
                "filename": "OVERRIDE_filename",
                "source": None,
            },
        ]
    )
    CM.store_cache_metadata(cache_dir, new_metadata)
    new_stored_metadata = CM.load_cache_metadata(cache_dir)

    assert (original_stored_metadata.columns == new_stored_metadata.columns).all()


def test_suppress_save_warnings(cache_dir, mocker):
    """Test that we can suppress warnings when saving metadata"""
    mocked_warning = mocker.patch("yaht.cache_management.logging.warning")
    # No warning should be called if warnings is set to false
    too_few_columns = pd.DataFrame([{"hash": "SOME_HASH"}])
    CM.store_cache_metadata(cache_dir, too_few_columns, warnings=False)
    mocked_warning.assert_not_called()


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
            "source": ["some-MaDe*uP/Source"],
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
