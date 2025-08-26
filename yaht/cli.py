#!/usr/bin/env python3
import os
import yaml
import shutil
import argparse
from matplotlib import pyplot as plt
from yaht.defaults import *
from yaht.config_processing import read_config_file
from yaht.processes import find_processes
from yaht.outputs import output_results, find_outputs
from yaht.laboratory import Laboratory


def cli():
    """Parse arguments and run experiments"""
    parser = argparse.ArgumentParser(
        prog="Yaht",
        description="Yet another hyperparameter tuner",
    )
    parser.add_argument("--config", help="Set custom config path")
    parser.add_argument("--cache", help="Set custom cache path")

    subparsers = parser.add_subparsers(dest="command")
    # Init subcommand to scaffold a directory for yaht
    init_parser = subparsers.add_parser("init", help="Scaffold current folder for yaht")
    # Add file subcommand to add files to the cache
    add_file_parser = subparsers.add_parser("add", help="Add a file to the cache")
    add_file_parser.add_argument("path", help="File to add")
    add_file_parser.add_argument(
        "-m",
        "--move",
        help="Delete original file",
        action="store_true",
    )
    # Run parser to run experiments
    run_parser = subparsers.add_parser(
        "run", help="Run experiments specified in the config"
    )
    # Results parser to get previous results
    result_parser = subparsers.add_parser("results", help="Output latest results")

    args = parser.parse_args()
    # Execute relevant commands
    if args.command == "init":
        gen_scaffold()
    if args.command == "add":
        add_file(args.path)
    if args.command == "run":
        find_processes()
        run_experiments()
    if args.command == "results":
        find_outputs()
        output_experiment_results()


def gen_scaffold(config_file=DEFAULT_CONFIG_FILE, cache_dir=DEFAULT_CACHE_DIR):
    """Generate a scaffold in the current working directory"""
    # Set the config file and cache dir from env variables if necessary
    if config_file == DEFAULT_CONFIG_FILE:
        config_file = os.environ.get("YAHT_CONFIG_FILE", DEFAULT_CONFIG_FILE)
    if cache_dir == DEFAULT_CACHE_DIR:
        cache_dir = os.environ.get("YAHT_CACHE_DIR", DEFAULT_CACHE_DIR)

    # Create base files
    os.mkdir(cache_dir)
    with open(config_file, "w") as f:
        f.write(DEFAULT_CONFIG)

    # Add relevant line to .gitignore if necessary
    if not os.path.exists(".git/"):
        return
    with open(".gitignore", "a") as f:
        f.write("\n\n" + cache_dir)


def add_file(
    file_path, move=False, config_file=DEFAULT_CONFIG_FILE, cache_dir=DEFAULT_CACHE_DIR
):
    """Add a new file to the cache and config by its path"""
    file_dir, file_name = os.path.split(file_path)

    # Set the config file and cache dir from env variables if necessary
    if config_file == DEFAULT_CONFIG_FILE:
        config_file = os.environ.get("YAHT_CONFIG_FILE", DEFAULT_CONFIG_FILE)
    if cache_dir == DEFAULT_CACHE_DIR:
        cache_dir = os.environ.get("YAHT_CACHE_DIR", DEFAULT_CACHE_DIR)

    # Move or copy the file
    target_path = os.path.join(cache_dir, file_name)
    print("Moving file %s to %s" % (file_path, target_path))
    if move:
        shutil.move(file_path, target_path)
    else:
        shutil.copy(file_path, target_path)

    # Add the file to the config
    with open(config_file, "r") as config_stream:
        config = yaml.safe_load(config_stream)
    if not config.get("SOURCES"):
        config["SOURCES"] = {}
    config["SOURCES"] |= {file_name: "file:%s" % file_name}
    with open(config_file, "w") as config_stream:
        yaml.dump(config, config_stream, default_flow_style=False)


def run_experiments(config_file=DEFAULT_CONFIG_FILE, cache_dir=DEFAULT_CACHE_DIR):
    """Run all the experiments specified in the config file"""
    config = read_config_file(config_file)
    lab = Laboratory(config)
    # Run the experiments
    lab.run_experiments()


def output_experiment_results(config_file=DEFAULT_CONFIG_FILE):
    """Load the results from any experiments performed as defined in the config file"""
    config = read_config_file(config_file)
    lab = Laboratory(config)
    # Get the results and pass them to output functions
    results = lab.get_results()
    output_results(results)


if __name__ == "__main__":
    cli()
