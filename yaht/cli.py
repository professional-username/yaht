#!/usr/bin/env python3
import argparse
from matplotlib import pyplot as plt
from yaht.config_processing import read_config_file
from yaht.result_handling import plot_results
from yaht.processes import find_processes
from yaht.laboratory import Laboratory


def cli():
    """Parse arguments and run experiments"""
    parser = argparse.ArgumentParser(
        prog="Yaht",
        description="Yet another hyperparameter tuner",
    )
    parser.add_argument("config")
    parser.add_argument("-R", "--run", action="append", nargs="*")
    parser.add_argument("-r", "--results", action="store_true")
    parser.add_argument("-a", "--add-file")
    args = parser.parse_args()

    # Import all python files in current folder to register processes
    find_processes()

    # First read the config
    config_file = args.config
    print("Config file: {}".format(config_file))
    config = read_config_file(config_file)

    # Create the laboratory
    lab = Laboratory(config)

    # Run experiments
    if args.run:
        lab.run_experiments()

    # Process results
    if args.results:
        results = lab.get_results()
        plot_results(results)
        plt.show()


if __name__ == "__main__":
    cli()
