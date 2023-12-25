#!/usr/bin/env python3
import os
import re
import shutil
import pickle
import sqlite3
import logging
import datetime
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
        "time_created": time_created,
        "time_modified": time_modified,
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
        metadata.to_csv(metadata_path)
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
        # Send warnings if this is necessary
        if warnings:
            if len(extra_columns) > 0:
                logging.warning("Tried to store metadata columns %s", extra_columns)
            if len(missing_columns) > 0:
                logging.warning("Missing metadata columns %s", missing_columns)

    # Combine with existing metadata
    metadata = load_cache_metadata(cache_dir)
    metadata = (
        metadata.set_index("hash")
        .combine(new_metadata.set_index("hash"), lambda x, y: y if y.any() else x)
        .reset_index()
    )

    # Save the new metadata
    metadata_path = os.path.join(cache_dir, METADATA_FILE)
    metadata.to_csv(metadata_path)


def update_cache_filenames(cache_dir):
    """Update the filenames of files in the cache based on metadata"""
    # First load the existing ones
    metadata = load_cache_metadata(cache_dir)
    filenames = metadata["filename"]
    # Then generate what they chould be
    hashes = metadata["hash"]
    sources = metadata["source"]
    source_to_fname = lambda x: re.sub(r"[^a-zA-Z0-9]", "_", x.lower())
    expected_filenames = sources.apply(source_to_fname) + "_" + hashes.str.slice(0, 4)

    # Find the filenames that don't match
    filename_mask = filenames != expected_filenames
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
