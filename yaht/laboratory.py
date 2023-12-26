#!/usr/bin/env python3
import pandas as pd
import yaht.cache_management as CM
from yaht.structure import generate_laboratory_structure

# from yaht.experiment import Experiment, generate_experiment_structure


class Laboratory:
    def __init__(self, config):
        # Get and set up general settings etc
        settings = config.get("settings", {})
        self.cache_dir = settings.get("cache_dir", None)
        self.existing_metadata = CM.load_cache_metadata(self.cache_dir)

        # Make sure all sources are stated as hashes
        source_hashes = config.get("sources", {})
        for key, value in source_hashes.items():
            source_hashes[key] = self.get_source_hash(value)
        # Generate the lab structure
        structure_config = {}
        structure_config["source_hashes"] = source_hashes
        structure_config["experiments"] = config["experiments"]
        self.structure = generate_laboratory_structure(structure_config)

        # Setup internal data storage
        self.internal_data = {}

    def get_source_hash(self, source_hash):
        """Turn a reference to a source into its hash"""
        (hash_type, hash_label, *_) = source_hash.split(":")
        match hash_type:
            case "hash":
                return hash_label
            case "file":
                return self.existing_metadata.set_index("filename").loc[
                    hash_label, "hash"
                ]
            case _:
                raise ValueError("Unknown hash type %s" % hash_type)

    def run_experiments(self):
        """Run every process that needs running"""
        self.determine_unrun_processes()  # First check which processes need running
        # Sort by experiment, trial and order, and then run
        sorted_structure = self.structure.sort_values(
            by=["experiment", "trial", "order"]
        )
        for idx, proc_row in sorted_structure.iterrows():
            if proc_row["has_run"]:
                continue
            # Extract all relevant parameters and run the process
            source_data = [self.get_data(h) for h in proc_row["source_hashes"]]
            proc_params = proc_row["params"]
            proc_function = proc_row["function"]
            result_hashes = proc_row["result_hashes"]
            result_data = proc_function(*source_data, **proc_params)
            # If there is only one result, the result is placed in a list of one
            if len(result_hashes) == 1:
                result_data = [result_data]
            for h, d in zip(result_hashes, result_data):
                self.set_data(h, d)

    def get_data(self, data_hash):
        """First try to get the data from internal storage, then the cache"""
        if data_hash in self.internal_data:
            return self.internal_data[data_hash]
        else:
            data = CM.load_cache_data(self.cache_dir, data_hash)
            self.internal_data[data_hash] = data
            return data

    def set_data(self, data_hash, data):
        self.internal_data[data_hash] = data
        CM.store_cache_data(self.cache_dir, data_hash, data)

    def determine_unrun_processes(self):
        """Check which of the processes in the structure need to be run"""
        metadata = CM.load_cache_metadata(self.cache_dir)
        verify_hash = lambda r_hashes: min(
            [r_h in metadata["hash"] for r_h in r_hashes]
        )  # We chack the result hashes of every process against existing data
        self.structure["has_run"] = self.structure["result_hashes"].apply(verify_hash)

    def get_results(self):
        """Return the result of every process that is marked as 'result'"""
        result_df = pd.DataFrame(
            columns=["experiment", "trial", "process", "name", "value"]
        )
        for idx, proc_row in self.structure.iterrows():
            # For every row, check if there are any results marked as experimental results
            result_indeces = [i for (i, r) in enumerate(proc_row["results"]) if r]
            if len(result_indeces) == 0:
                continue
            # If so, find them and retrieve them
            result_hashes = [proc_row["result_hashes"][idx] for idx in result_indeces]
            results = [self.get_data(h) for h in result_hashes]
            # Then add them to the result_df
            new_rows = pd.DataFrame({"value": results})
            new_rows["experiment"] = proc_row["experiment"]
            new_rows["trial"] = proc_row["trial"]
            new_rows["process"] = proc_row["name"]
            new_rows["name"] = proc_row["result_names"]
            result_df = pd.concat([result_df, new_rows], ignore_index=True)
        return result_df
