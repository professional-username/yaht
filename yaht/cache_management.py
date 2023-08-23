#!/usr/bin/env python3
import os
import shutil
import pickle
import sqlite3


class CacheIndex:
    def __init__(self, cache_dir):
        # Create the cache dir if necessary
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
        # Connect to or create the sqlite db
        index_fname = "cacheIndex"
        index_path = os.path.join(cache_dir, index_fname)
        self.connection = sqlite3.connect(index_path)
        # Create the tables in the db if they don't exist
        create_table_query = """
        CREATE TABLE IF NOT EXISTS CachedData (
            hash_id TEXT PRIMARY KEY NOT NULL,
            filename TEXT,
            source TEXT
        );"""
        cursor = self.connection.cursor()
        cursor.execute(create_table_query)

    def add_item(self, key, metadata={}):
        """Add a new item to the index"""
        expected_metadata = ["source"]
        for em in expected_metadata:
            if em not in metadata:
                metadata[em] = None

        # Generate the filename based on the source
        if "filename" in metadata:
            filename = metadata["filename"]
        elif metadata["source"]:
            filename = metadata["source"] + key[:5]
        else:
            filename = key

        # Store the key and the relevant metadata
        add_item_query = """
        INSERT INTO CachedData
        VALUES ('%s', '%s', '%s');
        """ % (
            key,
            filename,
            metadata["source"],
        )

        cursor = self.connection.cursor()
        cursor.execute(add_item_query)

    def delete_item(self, key):
        """Delete an item from the index"""
        delete_item_query = (
            """
        DELETE FROM CachedData
        WHERE hash_id = '%s'
        """
            % key
        )
        cursor = self.connection.cursor()
        cursor.execute(delete_item_query)

    def check_item_exists(self, key):
        """Check whether a key exists in the db"""
        check_query = (
            """
        SELECT 1
        FROM CachedData
        WHERE hash_id = '%s'
        """
            % key
        )
        cursor = self.connection.cursor()
        cursor.execute(check_query)
        data = cursor.fetchall()
        return len(data) > 0

    def get_item_metadata(self, key, column):
        """Get the metadata associated with the given key"""
        get_legend_query = """
        SELECT %s
        FROM CachedData
        WHERE hash_id='%s';
        """ % (
            column,
            key,
        )
        cursor = self.connection.cursor()
        cursor.execute(get_legend_query)
        metadata = cursor.fetchone()[0]
        return metadata

    def get_keys_by_metadata(self, data, column):
        """Get the keys that have the given metadata"""
        get_legend_query = """
        SELECT hash_id
        FROM CachedData
        WHERE %s='%s';
        """ % (
            column,
            data,
        )
        cursor = self.connection.cursor()
        cursor.execute(get_legend_query)
        keys = [key[0] for key in cursor.fetchall()]
        return keys


class CacheManager:
    def __init__(self, cache_dir):
        """Connect to the cache, initialize it if necessary"""
        self.cache_index = CacheIndex(cache_dir)
        self.cache_dir = cache_dir

    def send_data(self, key, data, metadata={}):
        """Save the data and record its metadata in the cache index"""
        # Create a new item if it doesn't exist
        if not self.cache_index.check_item_exists(key):
            self.cache_index.add_item(key, metadata)
        # Write the data to the relevant filename
        filename = self.cache_index.get_item_metadata(key, "filename")
        path = os.path.join(self.cache_dir, filename)
        with open(path, "wb") as f:
            pickle.dump(data, f)

    def add_file(self, source_file):
        """Add an external file to the cache"""
        # Load the data, then write it to the cache TODO This might be inefficient
        # with open(filename, "rb") as f:
        #     data = pickle.load(f)
        # Copy the file to the cache
        filename = source_file.split("/")[-1]
        cache_file = os.path.join(self.cache_dir, filename)
        shutil.copy(source_file, cache_file)
        # When adding an existing file, use the filename as the hash key
        metadata = {
            "filename": filename,
            "source": "file://" + source_file,
        }
        self.cache_index.add_item(filename, metadata)

    def get_data(self, key):
        """Load the data from the cache by the given key"""
        filename = self.cache_index.get_item_metadata(key, "filename")
        path = os.path.join(self.cache_dir, filename)
        with open(path, "rb") as f:
            data = pickle.load(f)
        return data

    def get_metadata(self, key, column):
        return self.cache_index.get_item_metadata(key, column)

    def get_keys_by_metadata(self, data, column):
        return self.cache_index.get_keys_by_metadata(data, column)

    def check_data(self, key):
        return self.cache_index.check_item_exists(key)

    def delete_data(self, key):
        """Delete the data file and relevant cache index entry"""
        if not self.cache_index.check_item_exists(key):
            return

        filename = self.cache_index.get_item_metadata(key, "filename")
        path = os.path.join(self.cache_dir, filename)
        os.remove(path)
        self.cache_index.delete_item(key)
