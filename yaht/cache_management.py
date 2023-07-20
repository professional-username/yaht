#!/usr/bin/env python3
import os


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
