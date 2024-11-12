#!/usr/bin/env python3
import os
import yaml
import shutil
import argparse
from matplotlib import pyplot as plt
from yaht.config_processing import read_config_file
from yaht.result_handling import plot_results
from yaht.processes import find_processes
from yaht.laboratory import Laboratory

DEFAULT_CONFIG_FILE = "yaht.yaml"
DEFAULT_CACHE_DIR = ".yaht_cache"

DEFAULT_CONFIG = """
SOURCES:
  zero: "value:0"

some_experiment:
  results: example_function
"""


def cli():
    """Parse arguments and run experiments"""
    parser = argparse.ArgumentParser(
        prog="Yaht",
        description="Yet another hyperparameter tuner",
    )
    subparsers = parser.add_subparsers(dest="command")
    # Init subcommand to scaffold a directory for yaht
    init_parser = subparsers.add_parser("init", help="Scaffold yaht.yaml etc")
    # TODO: run command, add_file command
    # ALso TODO: Default functions / values
    # Also? : Result functions

    args = parser.parse_args()

    if args.command == "init":
        gen_scaffold()


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


if __name__ == "__main__":
    cli()
