#!/usr/bin/env python3
import inspect
import itertools
import pandas as pd
import networkx as nx
from hashlib import sha256
from yaht.processes import get_process


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


def generate_experiment_structure(config):
    """
    Generate the structure of an experiment given a config
    in the form of a pandas dataframe
    """
    experiment_structure = pd.DataFrame()

    # Assemble the parameters for each trial
    global_params = config["parameters"] if "parameters" in config else {}
    trial_configs = config["trials"] if "trials" in config else {}
    trial_configs["control"] = {}
    for trial in trial_configs:
        trial_configs[trial] = global_params | trial_configs[trial]

    # Generate the config for each trial
    input_hashes = config["inputs"]
    trial_process_structure = config["structure"]
    for trial_name, trial_params in trial_configs.items():
        trial_config = {
            "inputs": input_hashes,
            "structure": trial_process_structure,
            "parameters": trial_params,
        }
        trial_structure = generate_trial_structure(trial_config)
        trial_structure["trial"] = trial_name  # Set the trial name of each process
        experiment_structure = pd.concat(
            [experiment_structure, trial_structure], ignore_index=True
        )

    # Set the output flag for each process
    output_procs = config["outputs"]
    experiment_structure["output"] = experiment_structure["name"].apply(
        lambda x: x in output_procs
    )

    return experiment_structure


def generate_trial_structure(config):
    """Generate a structure dataframe with a row for each process"""
    # Extract the different parts of the config
    params = config["parameters"] if "parameters" in config else {}
    structure = override_structure(config["structure"], params)

    # Convert the config to a simpler dependency structure
    proc_dependencies = get_proc_dependencies(structure)
    proc_names = get_organized_proc_names(proc_dependencies)
    proc_order = {proc_names[i]: i for i in range(len(proc_names))}
    # Get the function for each process
    proc_functions = get_proc_functions(structure)
    # Extract the parameters relevant to each process
    proc_params = get_proc_params(proc_functions, params)

    # # Generate the hashes for each process
    # proc_hashes = get_proc_hashes(
    #     proc_names, proc_params, proc_dependencies, input_hashes
    # )
    # dep_hashes = gen_dependency_hashes(proc_dependencies, proc_hashes, input_hashes)

    # Put all the parameters into a df
    structure_df = pd.DataFrame.from_dict(
        {
            # "hash": proc_hashes,
            "function": proc_functions,
            "order": proc_order,
            "params": proc_params,
            "deps": proc_dependencies,
            # "dep_hashes": dep_hashes,
        }
    )

    # Generate hashes for the processes and their dependencies
    input_hashes = config["inputs"] if "inputs" in config else []
    structure_df = gen_structure_hashes(structure_df, input_hashes)

    # Pull the proc names the structure is indexed by into their own column
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


def gen_structure_hashes(structure_df, input_hashes):
    """
    Hash the dependencies of each process,
    and then hash the processes themselves
    """
    # Order the structure based on the order the processes must be run in
    structure_df.sort_values("order", inplace=True)
    hash_df = pd.DataFrame(columns=["hash", "dep_hashes"])

    for process in structure_df.iterrows():
        # The process function, params and hashes of dependencies
        # are used to generate a process' hash
        proc_name = process[0]
        proc_deps = process[1]["deps"]
        proc_params = process[1]["params"]
        proc_function = process[1]["function"]

        # Store the hash of a process, as well as the hashes of its dependencies
        hash_df.loc[proc_name, "dep_hashes"] = []

        proc_hash = sha256(str(proc_function).encode())
        for param_item in proc_params.items():
            proc_hash.update(str(param_item).encode())
        for dep in proc_deps:
            [dep_name, *dep_index] = dep.split(".")
            dep_index = int(dep_index[0]) if dep_index else None
            # Input hashes have to be retrieved from their own dictionary
            # TODO is there a better way?
            if dep_name == "inputs":
                # If loading an input hash, get it from the given dict
                dep_hash = input_hashes[dep_index]
            else:
                # Otherwise look for a previously claculated hash,
                dep_hash = hash_df.loc[dep_name, "hash"]
                # and include the index if it exists
                dep_hash += "." + str(dep_index) if dep_index != None else ""
            # Save the dependency hashes as well as adding them to the process hash
            hash_df.loc[proc_name, "dep_hashes"].append(dep_hash)
            proc_hash.update(dep_hash.encode())

        # Save the assembled hash
        hash_df.loc[proc_name, "hash"] = proc_hash.hexdigest()

    # Return the combined df
    structure_df = pd.concat([structure_df, hash_df], axis=1)
    return structure_df
