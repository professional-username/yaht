#!/usr/bin/env python3
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
        results = {}
        for exp_name in self.experiments:
            results[exp_name] = self.experiments[exp_name].get_outputs()
        self.data_exporter.export_data(results)

    def set_data(self, key, value):
        data = {"data": value, "legend": str(value)}
        self.cache_manager.send_data(key, data)

    def get_data(self, key):
        return self.cache_manager.get_data(key)["data"]

    def check_data(self, key):
        return self.cache_manager.cache_index.check_item_exists(key)
