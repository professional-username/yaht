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
    "sources",
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
    with open(os.path.join(cache_dir, data_filename), "wb") as data_file:
        pickle.dump(data, data_file)

    # Save relevant meatadata
    new_metadata = pd.DataFrame.from_dict({"hash": [data_hash]}, orient="columns")
    store_cache_metadata(cache_dir, new_metadata)


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
        metadata = pd.read_csv(metadata_path, converters={"sources": pd.eval})
    # If the cache doesn't exist, create it
    except FileNotFoundError:
        metadata = pd.DataFrame(columns=METADATA_COLUMNS)
        os.makedirs(cache_dir, exist_ok=True)
        metadata.to_csv(metadata_path, index=False)

    # Some columns need to have specific datatypes
    metadata["hash"] = metadata["hash"].astype("string")
    metadata["filename"] = metadata["filename"].astype("string")
    metadata["time_created"] = pd.to_datetime(metadata["time_created"])
    metadata["time_modified"] = pd.to_datetime(metadata["time_modified"])

    return metadata


def store_cache_metadata(cache_dir, new_metadata):
    """Add one or more rows to the metadata"""
    # First verify that the columns match
    new_columns = list(new_metadata.columns)
    if new_columns != METADATA_COLUMNS:
        missing_columns = [c for c in METADATA_COLUMNS if c not in new_columns]
        # Resample the metadata to include the correct columns
        new_metadata[missing_columns] = None
        new_metadata = new_metadata[METADATA_COLUMNS]
        # Ensure columns abide to certain formatting
        new_metadata["hash"] = new_metadata["hash"].apply(str.strip)

    # Make sure columns have correct default values
    default_fname = lambda r: r["hash"] if pd.isnull(r["filename"]) else r["filename"]
    default_sources = lambda s: [] if type(s) is not list else s
    modified_time = datetime.datetime.now()
    default_time_modified = lambda t: modified_time
    default_time_created = lambda t: t if pd.notnull(t) else modified_time
    new_metadata["filename"] = new_metadata.apply(default_fname, axis=1)
    new_metadata["sources"] = new_metadata["sources"].apply(default_sources)
    new_metadata["time_modified"] = new_metadata["time_modified"].apply(
        default_time_modified
    )
    new_metadata["time_created"] = new_metadata["time_created"].apply(
        default_time_created
    )

    # Combine with existing metadata
    old_metadata = load_cache_metadata(cache_dir)
    metadata = combine_metadata(old_metadata, new_metadata)

    # Save the new metadata
    metadata_path = os.path.join(cache_dir, METADATA_FILE)
    metadata.to_csv(metadata_path, index=False)


def combine_metadata(old_metadata, new_metadata):
    """Combine existing metadata with new metadata column by column"""
    # Extract the hashes
    combined_hashes = list(set(list(old_metadata["hash"]) + list(new_metadata["hash"])))
    combined_metadata = pd.DataFrame(columns=METADATA_COLUMNS)
    combined_metadata["hash"] = combined_hashes
    # Set the index to be the hash
    combined_metadata = combined_metadata.set_index("hash")
    old_metadata = old_metadata.set_index("hash")
    new_metadata = new_metadata.set_index("hash")
    # Combine column by column
    for c in new_metadata.columns:
        old_column = old_metadata[c]
        new_column = new_metadata[c]
        combined_column = combine_metadata_columns(c, old_column, new_column)
        combined_metadata[c] = combined_column

    return combined_metadata.reset_index("hash")


def combine_metadata_columns(c_name, old_column, new_column):
    """Combine different columns based on the data they are supposed to store"""
    # Detrmine the merge function and default empty value for the column
    match c_name:
        case "sources":
            default_value = []
            combine_function = lambda old, new: list(set(old + new))
        case "time_created":
            default_value = pd.NaT
            combine_function = lambda old, new: min(old, new)
        case "time_modified":
            default_value = pd.NaT
            combine_function = lambda old, new: max(old, new)
        case _:
            default_value = np.nan
            combine_function = lambda old, new: new

    # But this will only apply to rows where both old and new columns have values
    is_empty = lambda x: (len(x) == 0) if type(x) == list else pd.isnull(x)
    merge_function = (
        # Default if both columns "empty"
        lambda r: (
            default_value
            if is_empty(r["new"]) and is_empty(r["old"])
            # If only one is empty, use non-empty one
            else (
                (r["new"] if is_empty(r["old"]) else r["old"])
                if is_empty(r["new"]) or is_empty(r["old"])
                # If both aren't empty, combine them as necessary
                else combine_function(r["old"], r["new"])
            )
        )
    )

    # Put the columns into a single df and combine
    old_new_df = pd.DataFrame({"old": old_column, "new": new_column})
    combined_column = old_new_df.apply(merge_function, axis=1)

    return combined_column


def update_cache_filenames(cache_dir):
    """Update the filenames of files in the cache based on metadata"""
    # First load the existing ones
    metadata = load_cache_metadata(cache_dir)
    filenames = metadata["filename"]
    # Then generate what they should be
    hashes = metadata["hash"]
    sources = metadata["sources"]
    # Hackyish fix to prune sources
    get_first_source = lambda s: s[0] if type(s) == list and len(s) > 0 else np.nan
    sources = sources.apply(get_first_source)
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
        # Hacky fix for file being the wrong name
        try:
            os.rename(fname_from, fname_to)
        except:
            continue

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
    store_cache_metadata(cache_dir, pd.DataFrame({"hash": unsaved_files}))
