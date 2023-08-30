#!/usr/bin/env python3
import pandas as pd
from yaht.cache_management import CacheManager
from yaht.experiment import Experiment, generate_experiment_structure


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

    def set_data(self, key, data, metadata):
        self.cache_manager.send_data(key, data, metadata)

    def get_data(self, key):
        data = self.cache_manager.get_data(key)
        return data

    def check_data(self, key):
        return self.cache_manager.cache_index.check_item_exists(key)

    def get_data_by_fname(self, fname):
        """Get some data from the cache based on the given fname"""
        key = self.cache_manager.get_keys_by_metadata(fname, "filename")[0]
        data = self.cache_manager.get_data(key)
        return data

    def export_experiment_results(self):
        """Get the results of every experiment and pass them to the experiment"""
        results = pd.DataFrame(columns=["data", "experiment", "trial", "process"])
        for exp_name in self.experiments:
            exp_results = self.experiments[exp_name].get_outputs()
            exp_results["experiment"] = exp_name
            results = pd.concat([results, exp_results], ignore_index=True)
        self.data_exporter.export_data(results)

    # def export_output_metadata(self, data_exporter):
    # """Get the metadata for each piece of output data and export it"""
    # output_keys = []
    # for exp_name in self.experiments:
    #     output_keys.append(self.experiments[exp_name])
    # metadata =


def generate_laboratory_structure(config):
    """Convert a nested dictionary config into a dataframe structure"""
    laboratory_structure = pd.DataFrame()

    # Generate every experiment structure
    input_files = config["input_files"] if "input_files" in config else {}
    experiment_configs = config["experiments"]
    for exp_name, exp_config in experiment_configs.items():
        # Substitute in the input hashes for each experiment TODO: Extract to seperate method?
        exp_inputs = exp_config["inputs"]
        input_hashes = []
        for exp_input in exp_inputs:
            input_type, input_name = exp_input.split(":")
            if input_type == "file":
                input_hash = input_files[input_name]
            elif input_type == "hash":
                input_hash = input_name
            else:
                raise ValueError("Invalid input type '%s'" % input_type)
            input_hashes.append(input_hash)
        # Generate the experimennt structure
        exp_config["inputs"] = input_hashes
        exp_structure = generate_experiment_structure(exp_config)
        # Set other values for the experiment
        exp_structure["experiment"] = exp_name
        # Append to the global lab structure
        laboratory_structure = pd.concat(
            [laboratory_structure, exp_structure], ignore_index=True
        )

    return laboratory_structure
