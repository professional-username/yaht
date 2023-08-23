#!/usr/bin/env python3
import pandas as pd
from yaht.cache_management import CacheManager
from yaht.experiment import Experiment


class Laboratory:
    def __init__(self, config, data_exporter):
        # Initialize relevant values
        self.data_exporter = data_exporter
        self.cache_manager = CacheManager(config["cache_dir"])
        self.experiments = {}
        for exp_name in config["experiments"]:
            exp_config = config["experiments"][exp_name]
            self.experiments[exp_name] = Experiment(exp_config, self)

    def run_experiments(self):
        # Run every experiment
        for exp_name in self.experiments:
            self.experiments[exp_name].run_trials()

    def export_experiment_results(self):
        """Get the results of every experiment and pass them to the experiment"""
        results = pd.DataFrame(columns=["data", "experiment", "trial", "process"])
        for exp_name in self.experiments:
            exp_results = self.experiments[exp_name].get_outputs()
            exp_results["experiment"] = exp_name
            results = pd.concat([results, exp_results], ignore_index=True)
        self.data_exporter.export_data(results)

    def set_data(self, key, value, metadata):
        data = {"data": value, "metadata": metadata}
        self.cache_manager.send_data(key, data, metadata)

    def get_data(self, key):
        return self.cache_manager.get_data(key)["data"]

    def check_data(self, key):
        return self.cache_manager.cache_index.check_item_exists(key)

    def get_data_by_fname(self, fname):
        """Get some data from the cache based on the given fname"""
        key = self.cache_manager.get_keys_by_metadata(fname, "filename")[0]
        data = self.cache_manager.get_data(key)
        return data
