#!/usr/bin/env python3
import networkx as nx
from yaht.processes import get_process


class Trial:
    def __init__(self, parent_experiment, config):
        self.parent_experiment = parent_experiment

        structure = config["structure"]
        params = config["parameters"] if "parameters" in config else {}
        self.proc_dependencies = structure
        self.proc_functions = {p: get_process(p) for p in structure}
        self.proc_names = self.get_organized_proc_names(structure)
        self.proc_hashes = {p: p for p in structure}
        # self.proc_params = self.get_proc_params

    def run(self):
        """Run the trial"""
        for proc in self.proc_names:
            input_data = self.get_data(self.proc_dependencies[proc])
            # params =
            output_data = self.proc_functions[proc](*input_data)
            self.set_data(proc, output_data)

    def set_data(self, proc, data):
        """Make calls to the parent experiment with the right keys"""
        data_hash = proc
        self.parent_experiment.set_data(data_hash, data)

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

    def get_organized_proc_names(self, structure):
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
