#!/usr/bin/env python3
import inspect
import itertools
import pandas as pd
import networkx as nx
from hashlib import sha256
from yaht.processes import get_process


class Trial:
    def __init__(self, parent_experiment, config):
        self.parent_experiment = parent_experiment

        params = config["parameters"] if "parameters" in config else {}
        # Override processes if given in functions
        structure = override_structure(config["structure"], params)

        # Convert the config to a simpler dependency structure
        self.proc_dependencies = get_proc_dependencies(structure)
        self.proc_names = get_organized_proc_names(self.proc_dependencies)
        # Get the function for each process
        self.proc_functions = get_proc_functions(structure)
        # Extract the parameters relevant to each process
        self.proc_params = get_proc_params(self.proc_functions, params)
        #
        # Hash each process based on its params and dependencies
        self.proc_hashes = self.get_proc_hashes(self.proc_names)

    def run(self):
        """Run the trial"""
        for proc in self.proc_names:
            # Don't run the process if its output already exists in the parent experiment
            proc_hash = self.proc_hashes[proc]
            data_exists = self.parent_experiment.check_data(proc_hash)
            if data_exists:
                continue

            input_data = self.get_data(self.proc_dependencies[proc])
            params = self.proc_params[proc]
            output_data = self.proc_functions[proc](*input_data, **params)
            self.set_data(proc, output_data)

    def set_data(self, proc, data):
        """Make calls to the parent experiment with the right keys"""
        # Get the relevant key for the proc
        data_hash = self.proc_hashes[proc]
        # Generate the metadata
        metadata = {}
        metadata["source"] = proc
        self.parent_experiment.set_data(data_hash, data, metadata)

    def get_data(self, sources):
        """Make calls to the parent experiment with the right keys"""
        data = []
        for src in sources:
            main_src = src.split(".")[0]
            # Handle inputs seperately
            if main_src == "inputs":
                subindex = int(src.split(".")[1])
                data_for_src = self.parent_experiment.get_input(subindex)
                data.append(data_for_src)
                continue

            # Otherwise, hash the source and get the relevant data
            data_hash = self.proc_hashes[main_src]
            data_for_src = self.parent_experiment.get_data(data_hash)
            # May need to subindex the retrieved data
            if len(src.split(".")) > 1:
                subindex = int(src.split(".")[1])
                data_for_src = data_for_src[subindex]
            data.append(data_for_src)

        return data

    def get_proc_hashes(self, proc_names):
        """
        Generate a unique hash for each process
        based on a its name, parameters and dependencies
        """
        proc_hashes = {}

        # Must iterate over the procs in order so dependencies are hashed first
        for proc in proc_names:
            # Hash each proc and its dependencies
            proc_hash = sha256(proc.encode())
            # Add parameter hashes
            for param_item in self.proc_params[proc].items():
                proc_hash.update(str(param_item).encode())
            # Add dependency hashes
            for dep in self.proc_dependencies[proc]:
                split_dep = dep.split(".")
                # The dep value is either either the dep hash of the hasehd input in the case of input
                if split_dep[0] == "inputs":
                    # NOTE: This may be too slow with large inputs,
                    # should experiment have an input_hash method?
                    dep_value = self.parent_experiment.get_input(split_dep[1])
                else:
                    dep_value = proc_hashes[split_dep[0]]
                # Hash the dep and update the proc hash
                dep_hash = str(dep_value).encode()
                proc_hash.update(dep_hash)
            proc_hashes[proc] = proc_hash.hexdigest()

        return proc_hashes
