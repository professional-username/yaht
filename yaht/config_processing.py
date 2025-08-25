#!/usr/bin/env python3
import yaml


def read_config_file(config_fname):
    """Read a yaml config file into a nested dictionary structure"""

    # First simply load the file into a dictionary
    with open(config_fname, "r") as config_stream:
        raw_config = yaml.safe_load(config_stream)

    # Then process every item in the config
    config = {
        "experiments": {},
    }
    for key, value in raw_config.items():
        # Top level-sections come in different types
        match key:
            case "SOURCES":
                config["sources"] = value
            case "SETTINGS":
                config["settings"] = value
            case "OUTPUTS":
                config["outputs"] = value
            # If they don't fall into one of the above categories,
            # they represent an experiment
            case _:
                config["experiments"][key] = process_experiment_config(value)

    return config


def process_experiment_config(raw_experiment_config):
    """Process the user-readable experiment config into program-readable"""
    experiment_config = {}

    # Structure
    raw_structure_config = raw_experiment_config["structure"]
    experiment_config["structure"] = process_structure_config(raw_structure_config)

    # Results
    results_string = raw_experiment_config.get("results", "")
    results_list = results_string.split(",")
    results_list = list(map(str.strip, results_list))
    experiment_config["results"] = results_list

    # Trials
    raw_trials_config = raw_experiment_config.get("trials", {})
    experiment_config["trials"] = raw_trials_config

    # Parameters
    raw_parameters_config = raw_experiment_config.get("parameters", {})
    experiment_config["parameters"] = raw_parameters_config

    return experiment_config


def process_structure_config(raw_structure_config):
    """
    Turn one-line process key-value pairs into dicts
    specifying the parameters of the process
    """
    structure_config = {}
    for key, value in raw_structure_config.items():
        # First generate the process name and function from the key
        proc_name = key.split("<-")[0]
        proc_function = key.split("<-")[1] if "<-" in key else proc_name

        # Then generate the sources and results from the value
        sources_string = value.split("->")[0].strip()
        sources_list = sources_string.split(",")
        results_string = value.split("->")[1] if "->" in value else proc_name
        results_list = results_string.split(",")

        # Strip all parameters of extraneous whitespace
        proc_name = proc_name.strip()
        proc_function = proc_function.strip()
        sources_list = list(map(str.strip, sources_list))
        results_list = list(map(str.strip, results_list))
        # Remove 'empty' sources and results
        sources_list = [s for s in sources_list if s != "_"]

        # Combine into a single process config and add to structure config
        structure_config[proc_name] = {
            "function": proc_function,
            "sources": sources_list,
            "results": results_list,
        }
    return structure_config
