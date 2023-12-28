#!/usr/bin/env python3
import os
import re
import shutil
import pickle
import sqlite3
import logging
import datetime
import numpy as np
import pandas as pd

METADATA_FILE = "metadata.csv"
METADATA_COLUMNS = [
    "hash",
    "filename",
    "source",
    "time_created",
    "time_modified",
]


def store_cache_data(cache_dir, data_hash, data):
    """Store the given data in the cache"""
    # Check if the data alread exists in the cache
    try:
        metadata = load_cache_metadata(cache_dir).set_index("hash").loc[data_hash]
        metadata = dict(metadata.dropna().items())
    except KeyError:
        metadata = {}

    # Create a file in the cache dir with the data
    data_filename = metadata.get("filename", data_hash)
    # data_filename = os.path.join(cache_dir, data_hash)
    with open(os.path.join(cache_dir, data_filename), "wb") as data_file:
        pickle.dump(data, data_file)

    # Generate the new metadata
    time_modified = datetime.datetime.now()
    time_created = metadata.get("time_created", time_modified)
    new_metadata = {
        "hash": [data_hash],
        "filename": [data_filename],
        "time_created": [time_created],
        "time_modified": [time_modified],
    }
    new_metadata = pd.DataFrame.from_dict(new_metadata, orient="columns")
    store_cache_metadata(cache_dir, new_metadata, warnings=False)


def load_cache_data(cache_dir, data_hash):
    """Load data from the cache"""
    # Retrieve the data filename from the metadata
    metadata = load_cache_metadata(cache_dir).set_index("hash").loc[data_hash]
    metadata = dict(metadata.dropna().items())
    data_filename = metadata.get("filename", data_hash)
    # Load the data from the cache
    with open(os.path.join(cache_dir, data_filename), "rb") as data_file:
        loaded_data = pickle.load(data_file)
    # Return the data
    return loaded_data


def load_cache_metadata(cache_dir):
    """
    Load the metadata for a cache,
    generating it if it doesn't exist
    """
    metadata_path = os.path.join(cache_dir, METADATA_FILE)
    try:
        metadata = pd.read_csv(metadata_path)
    # If the cache doesn't exist, create it
    except FileNotFoundError:
        metadata = pd.DataFrame(columns=METADATA_COLUMNS)
        os.mkdir(cache_dir)
        metadata.to_csv(metadata_path, index=False)
    # Some columns need to have specific datatypes
    metadata["time_created"] = pd.to_datetime(metadata["time_created"])
    metadata["time_modified"] = pd.to_datetime(metadata["time_modified"])
    return metadata


def store_cache_metadata(cache_dir, new_metadata, warnings=True):
    """Add one or more rows to the metadata"""
    # First verify that the columns match
    new_columns = list(new_metadata.columns)
    if new_columns != METADATA_COLUMNS:
        extra_columns = [c for c in new_columns if c not in METADATA_COLUMNS]
        missing_columns = [c for c in METADATA_COLUMNS if c not in new_columns]
        # Resample the metadata to include the correct columns
        new_metadata[missing_columns] = None
        new_metadata = new_metadata[METADATA_COLUMNS]
        # Ensure columns abide to certain formatting
        new_metadata["hash"] = new_metadata["hash"].apply(str.strip)
        # Send warnings if this is necessary
        if warnings:
            if len(extra_columns) > 0:
                logging.warning("Tried to store metadata columns %s", extra_columns)
            if len(missing_columns) > 0:
                logging.warning("Missing metadata columns %s", missing_columns)

    # Combine with existing metadata
    metadata = load_cache_metadata(cache_dir).set_index("hash")
    new_metadata = new_metadata.set_index("hash")
    metadata = new_metadata.combine_first(metadata)
    metadata = metadata.reset_index("hash")

    # Save the new metadata
    metadata_path = os.path.join(cache_dir, METADATA_FILE)
    metadata.to_csv(metadata_path, index=False)


def update_cache_filenames(cache_dir):
    """Update the filenames of files in the cache based on metadata"""
    # First load the existing ones
    metadata = load_cache_metadata(cache_dir)
    filenames = metadata["filename"]
    # Then generate what they should be
    hashes = metadata["hash"]
    sources = metadata["source"]
    source_to_fname = lambda x: re.sub(r"[^a-zA-Z0-9]", "_", str(x).lower())
    expected_filenames = sources.apply(source_to_fname)
    expected_filenames += "_" + hashes.str.slice(0, 4)
    # hacky fix for nans
    expected_filenames = expected_filenames.apply(
        lambda x: np.nan if x.startswith("nan") else x
    )

    # Find the filenames that don't match
    filename_mask = filenames != expected_filenames
    filename_mask = filename_mask & expected_filenames.apply(pd.notnull)
    filenames_from = filenames[filename_mask]
    filenames_to = expected_filenames[filename_mask]
    # Rename the relevant files
    for fname_from, fname_to in zip(filenames_from, filenames_to):
        fname_from = os.path.join(cache_dir, fname_from)
        fname_to = os.path.join(cache_dir, fname_to)
        os.rename(fname_from, fname_to)

    # Save the new filenames
    metadata["filename"] = expected_filenames
    store_cache_metadata(cache_dir, metadata)


def sync_cache_metadata(cache_dir):
    """
    Check through the files in the cache
    adding any new ones and deleting missing ones from the metadata
    """
    metadata = load_cache_metadata(cache_dir)
    recorded_files = metadata["filename"]
    files_in_cache = os.listdir(cache_dir)
    files_in_cache.remove(METADATA_FILE)
    # Remove missing file metadata
    missing_files = [f for f in recorded_files if f not in files_in_cache]
    if len(missing_files):
        metadata = metadata[~metadata["filename"].isin(missing_files)]
        metadata_path = os.path.join(cache_dir, METADATA_FILE)
        metadata.to_csv(metadata_path, index=False)
    # Add missing files
    unsaved_files = [f for f in files_in_cache if f not in recorded_files]
    time_modified = datetime.datetime.now()
    time_created = time_modified
    store_cache_metadata(
        cache_dir,
        pd.DataFrame(
            {
                "hash": unsaved_files,
                "filename": unsaved_files,
                "time_modified": time_modified,
                "time_created": time_created,
            }
        ),
    )
