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


def generate_trial_structure(config):
    """Generate a structure dataframe with a row for each process"""
    # Extract the different parts of the config
    params = config["parameters"] if "parameters" in config else {}
    input_hashes = config["inputs"] if "inputs" in config else []
    structure = override_structure(config["structure"], params)

    # Convert the config to a simpler dependency structure
    proc_dependencies = get_proc_dependencies(structure)
    proc_names = get_organized_proc_names(proc_dependencies)
    proc_order = {proc_names[i]: i for i in range(len(proc_names))}
    # Get the function for each process
    proc_functions = get_proc_functions(structure)
    # Extract the parameters relevant to each process
    proc_params = get_proc_params(proc_functions, params)
    # Generate the hashes for each process
    proc_hashes = get_proc_hashes(
        proc_names, proc_params, proc_dependencies, input_hashes
    )
    dep_hashes = gen_dependency_hashes(proc_dependencies, proc_hashes, input_hashes)

    # Put all the parameters into a df
    structure_df = pd.DataFrame.from_dict(
        {
            "hash": proc_hashes,
            "order": proc_order,
            "parameters": proc_params,
            "deps": proc_dependencies,
            "dep_hashes": dep_hashes,
            "function": proc_functions,
        }
    )
    structure_df.index.names = ["name"]
    structure_df = structure_df.reset_index()

    return structure_df


def get_proc_functions(structure):
    """Get the function relevant to each process 'name'"""
    proc_functions = {}
    for name in structure:
        # If the name is of the form "x <- y", the name is x, the process is y
        name = name.split("<-")
        proc_name = name[0].strip()
        function = name[-1].strip()
        proc_functions[proc_name] = get_process(function)

    return proc_functions


def get_proc_dependencies(structure):
    """Simplify the given structure into a dependency dict"""
    simplified_structure = {}
    for proc_name, proc_deps in structure.items():
        if "<-" in proc_name:
            proc_name = proc_name.split("<-")[0].strip()
        simplified_structure[proc_name] = proc_deps
    return simplified_structure


def get_proc_params(proc_functions, all_params):
    """Get the relevant parameters for each process in proc_functions"""
    all_proc_params = {}
    for proc_name, proc_function in proc_functions.items():
        proc_params = [
            param
            for param in inspect.signature(proc_function).parameters
            if param is not inspect.Parameter.empty
        ]
        # Read the params from all_params that apply to the given proc
        relevant_params = {p: all_params[p] for p in proc_params if p in all_params}
        override_params = {
            p: all_params["%s.%s" % (proc_name, p)]
            for p in proc_params
            if "%s.%s" % (proc_name, p) in all_params
        }
        relevant_params |= override_params
        all_proc_params[proc_name] = relevant_params

    return all_proc_params


def get_organized_proc_names(structure):
    """Organize processes and their dependencies with networkx"""
    proc_graph = nx.DiGraph()
    for proc, deps in structure.items():
        deps = [d.split(".")[0] for d in deps]  # Split off "sub-dependencies"
        for d in deps:
            proc_graph.add_edge(proc, d)
    # Use a topological sort to figure out the order procs must be run in
    sorted_procs = list(nx.topological_sort(proc_graph))
    sorted_procs.reverse()
    # Remove the "inputs" node, as it is not a process
    if "inputs" in sorted_procs:
        sorted_procs.remove("inputs")

    return sorted_procs


def override_structure(structure, params):
    """Override any parts of the structure that are specified by parameters"""
    override_procs = {
        p.split("<-")[0].strip(): [p, params[p]] for p in params if "<-" in p
    }
    overriden_procs = []
    for proc_name, override_proc in itertools.product(
        structure.keys(), override_procs.keys()
    ):
        if proc_name.startswith(override_proc):
            overriden_procs.append(proc_name)
            proc_name = override_procs[override_proc][0]
            proc_deps = override_procs[override_proc][1]
            structure[proc_name] = proc_deps

    # Delete the procs that were overriden from the original structure
    for p in overriden_procs:
        print(p)
        del structure[p]

    return structure


def get_proc_hashes(proc_names, proc_params, proc_dependencies, input_hashes):
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
        for param_item in proc_params[proc].items():
            proc_hash.update(str(param_item).encode())
        # Add dependency hashes
        for dep in proc_dependencies[proc]:
            split_dep = dep.split(".")
            # The dep value is either either the dep hash of the hasehd input in the case of input
            if split_dep[0] == "inputs":
                dep_value = input_hashes[int(split_dep[1])]
            else:
                dep_value = proc_hashes[split_dep[0]]
            # Hash the dep and update the proc hash
            dep_hash = str(dep_value).encode()
            proc_hash.update(dep_hash)
        proc_hashes[proc] = proc_hash.hexdigest()

    return proc_hashes


def gen_dependency_hashes(proc_dependencies, proc_hashes, input_hashes):
    """Turn every dependency into the appropriate hash"""
    dep_hashes = {}
    for proc in proc_dependencies:
        dep_hashes[proc] = []
        for dep in proc_dependencies[proc]:
            # Get the dependency hash
            split_dep = dep.split(".")
            if split_dep[0] == "inputs":
                dep_hash = input_hashes[int(split_dep[1])]
                split_dep = split_dep[:1]
            else:
                dep_hash = proc_hashes[split_dep[0]]
            split_dep[0] = dep_hash

            # Save it to the dictionary
            # TODO: Combine with get_proc_hashes?
            dep_hashes[proc].append(".".join(split_dep))
    return dep_hashes
