#!/usr/bin/env python3
import os
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
            legend TEXT
        );"""
        cursor = self.connection.cursor()
        cursor.execute(create_table_query)

    def add_item(self, key, legend=None):
        """Add a new item to the index"""
        if legend is None:
            legend = key

        # TODO: Generate a more useful filename
        filename = key

        add_item_query = """
        INSERT INTO CachedData
        VALUES ('%s', '%s', '%s');
        """ % (
            key,
            filename,
            legend,
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

    def get_item_legend(self, key):
        """Get the legend associated with the given key"""
        return self.get_item_parameter(key, "legend")

    def get_item_filename(self, key):
        """Get the filename associated with the given key"""
        return self.get_item_parameter(key, "filename")

    def get_item_parameter(self, key, parameter):
        """Get the parameter associated with the given key"""
        get_legend_query = """
        SELECT %s
        FROM CachedData
        WHERE hash_id='%s';
        """ % (
            parameter,
            key,
        )
        cursor = self.connection.cursor()
        cursor.execute(get_legend_query)
        param = cursor.fetchone()[0]
        return param


class CacheManager:
    def __init__(self, cache_dir):
        """Connect to the cache, initialize it if necessary"""
        self.cache_index = CacheIndex(cache_dir)

    def send_data(self, key, data):
        """Save the data and record its metadata in the cache index"""
        # Create a new item if it doesn't exist
        if not self.cache_index.check_item_exists(key):
            self.cache_index.add_item(key, data["legend"])
        # Write the data to the relevant filename
        filename = self.cache_index.get_item_filename(key)
        with open(filename, "wb") as f:
            pickle.dump(data["data"], f)

    def get_data(self, key):
        """Load the data from the cache by the given key"""
        filename = self.cache_index.get_item_filename(key)
        with open(filename, "rb") as f:
            raw_data = pickle.load(f)
        data_legend = self.cache_index.get_item_legend(key)
        data = {"data": raw_data, "legend": data_legend}
        return data

    def check_data(self, key):
        return self.cache_index.check_item_exists(key)

    def delete_data(self, key):
        """Delete the data file and relevant cache index entry"""
        if not self.cache_index.check_item_exists(key):
            return

        filename = self.cache_index.get_item_filename(key)
        os.remove(filename)
        self.cache_index.delete_item(key)
