#!/usr/bin/env python3
import os
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
        self.cache_dir = cache_dir
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)

        # Create or connect to the cache index
        self.reload_index()

        self.data = {}

    def reload_index(self):
        """Connect to the index that stores cache descriptors etc"""
        pass

    def send_data(self, key, data):
        self.data[key] = data

    def get_data(self, key):
        return self.data[key]
