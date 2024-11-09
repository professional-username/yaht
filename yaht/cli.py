#!/usr/bin/env python3
import os
import argparse
from matplotlib import pyplot as plt
from yaht.config_processing import read_config_file
from yaht.result_handling import plot_results
from yaht.processes import find_processes
from yaht.laboratory import Laboratory

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
    subparsers = parser.add_subparsers()
    # Init subcommand to scaffold a directory for yaht
    init_parser = subparsers.add_parser("init", help="Scaffold yaht.yaml etc")
    # TODO: run command, add_file command

    args = parser.parse_args()

    if args.command == "init":
        gen_scaffold()


def gen_scaffold():
    """Generate a scaffold in the current working directory"""
    # Create base files
    os.mkdir(".yaht_cache/")
    with open("yaht.yaml", "w") as f:
        f.write(DEFAULT_CONFIG)

    # Add relevant line to .gitignore if necessary
    if not os.path.exists(".git/"):
        return
    with open(".gitignore", "a") as f:
        f.write(".yaht_cache")


if __name__ == "__main__":
    cli()
