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
    params = config.get("parameters", {})
    structure = override_structure(config["structure"], params)

    # Convert the config to a simpler dependency structure
    proc_sources = get_proc_source_names(structure)
    proc_results = get_proc_result_names(structure)
    # And extract the order procs should be run it
    proc_names = get_organized_proc_names(proc_sources, proc_results)
    proc_order = {proc_names[i]: i for i in range(len(proc_names))}
    # Get the function for each process
    proc_functions = get_proc_functions(structure)
    # Extract the parameters relevant to each process
    proc_params = get_proc_params(proc_functions, params)

    # Put all the parameters into a df
    structure_df = pd.DataFrame.from_dict(
        {
            "function": proc_functions,
            "order": proc_order,
            "params": proc_params,
            "source_names": proc_sources,
            "result_names": proc_results,
        }
    )

    # Generate hashes for the processes and their dependencies
    source_hashes = config.get("source_hashes", {})
    structure_df = gen_structure_hashes(structure_df, source_hashes)

    # Pull the proc names the structure is indexed by into their own column
    structure_df.index.names = ["name"]
    structure_df = structure_df.reset_index()

    return structure_df


def get_proc_functions(structure):
    """Get the function relevant to each process 'name'"""
    proc_functions = {}
    for proc_name, proc_config in structure.items():
        # If the function isn't specified, assume it's the same as the proc_name
        function_name = proc_config.get("function", proc_name)
        proc_functions[proc_name] = get_process(function_name)

    return proc_functions


def get_proc_source_names(structure):
    """Simplify the given structure into a dependency dict"""
    simplified_structure = {}
    for proc_name, proc_config in structure.items():
        simplified_structure[proc_name] = proc_config.get("sources")
    return simplified_structure


def get_proc_result_names(structure):
    """Extract the result names for each process"""
    simplified_structure = {}
    for proc_name, proc_config in structure.items():
        # If the results aren't specified,
        # assume it's a single one with the same name as the function
        simplified_structure[proc_name] = proc_config.get("results", [proc_name])
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


def get_organized_proc_names(structure, proc_results):
    """Organize processes and their dependencies with networkx"""
    proc_graph = nx.DiGraph()
    for proc_name, proc_sources in structure.items():
        # Find the processes the proc_sources refer to; e.g. foo.model should find foo
        proc_source_procs = []
        for source_name in proc_sources:
            source_proc = next(
                (
                    proc
                    for proc, results in proc_results.items()
                    if source_name in results
                ),
                "INPUT",
            )
            proc_source_procs.append(source_proc)
        # Organize into a process graph
        for source_proc in proc_source_procs:
            proc_graph.add_edge(proc_name, source_proc)
    # Use a topological sort to figure out the order procs must be run in
    sorted_procs = list(nx.topological_sort(proc_graph))
    sorted_procs.reverse()
    # Remove the "inputs" node, as it is not a process
    if "INPUT" in sorted_procs:
        sorted_procs.remove("INPUT")

    return sorted_procs


def override_structure(structure, parameters):
    """Override any parts of the structure that are specified by parameters"""
    for param in parameters:
        if "." not in param:
            continue
        proc_name, param_name = param.split(".", 1)
        match param_name:
            case "SOURCES":
                struct_component = "sources"
            case "FUNCTION":
                struct_component = "function"
            case "RESULTS":
                struct_component = "results"
            case _:
                continue
        structure[proc_name][struct_component] = parameters[param]

    return structure


def gen_structure_hashes(structure_df, source_hashes):
    """
    Hash the dependencies of each process,
    and then hash the processes themselves
    """
    # Order the structure based on the order the processes must be run in
    structure_df.sort_values("order", inplace=True)
    hash_df = pd.DataFrame(columns=["result_hashes", "source_hashes"])

    for process in structure_df.iterrows():
        # The process function, params and hashes of dependencies
        # are used to generate a process' hash
        proc_name = process[0]
        proc_sources = process[1]["source_names"]
        proc_params = process[1]["params"]
        proc_function = process[1]["function"]
        # A seperate hash is generated for each result
        proc_results = process[1]["result_names"]

        # First retrieve and save the source hashes
        proc_source_hashes = [source_hashes.get(s) for s in proc_sources]
        hash_df.loc[proc_name, "source_hashes"] = proc_source_hashes
        # Then generate and save the result hashes
        proc_hash = sha256(str(proc_function).encode())
        proc_hash.update(str(source_hashes).encode())
        proc_hash.update(str(proc_params).encode())
        proc_result_hashes = [proc_hash.copy() for r in proc_results]
        for i, r in enumerate(proc_results):
            proc_result_hashes[i].update(str(r).encode())
            proc_result_hashes[i] = str(proc_result_hashes[i].hexdigest())
        hash_df.loc[proc_name, "result_hashes"] = proc_result_hashes

        # Also save the result hashes to be used as source hashes for other procs
        for source_name, source_hash in zip(proc_results, proc_result_hashes):
            source_hashes[source_name] = source_hash

    # Return the combined df
    structure_df = pd.concat([structure_df, hash_df], axis=1)
    return structure_df
