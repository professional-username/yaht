import yaml
import networkx as nx
from yaht.processes import get_process


class Experiment:
    def __init__(self, config):
        """Read a yaml config from a string and setup the experiment"""
        self.assemble_experiment(config)
        self.read_inputs(config)
        self.output_deps = config["outputs"]

        self.data = {"inputs": self.inputs}

    def assemble_experiment(self, config):
        self.proc_deps = config["structure"]
        self.proc_names = self.get_organized_proc_names(self.proc_deps)
        self.processes = {p: get_process(p) for p in self.proc_names}

    # TODO: Possiby unnecessary as its own method
    def get_organized_proc_names(self, structure):
        """Organize processes and their dependencies with networkx"""
        proc_graph = nx.DiGraph()
        for proc, deps in structure.items():
            deps = [d.split(".")[0] for d in deps]  # Split off "sub-dependencies"
            for d in deps:
                if d == "inputs":
                    continue
                proc_graph.add_edge(proc, d)
        # Use a topological sort to figure out the order procs must be run in
        sorted_procs = list(nx.topological_sort(proc_graph))
        sorted_procs.reverse()
        return sorted_procs

    def run(self):
        """Run the methods in the experiment"""
        for proc_name in self.proc_names:
            deps = self.proc_deps[proc_name]
            # TODO: This is ugly
            data = self.get_data(deps)

            outputs = self.processes[proc_name](*data)
            self.data[proc_name] = outputs

    # TODO: Possiby unnecessary as its own method
    def get_data(self, dependencies):
        data = []

        for dep in dependencies:
            # Check if we're referencing a specific subset of data
            main_dep = dep.split(".")[0]
            data_for_dep = self.data[main_dep]

            if len(dep.split(".")) > 1:
                subindex = int(dep.split(".")[1])
                data_for_dep = data_for_dep[subindex]

            data.append(data_for_dep)

        return data

    def read_inputs(self, config):
        self.inputs = config["inputs"]

    def get_outputs(self):
        """Get the output of the experiment"""
        outputs = self.get_data(self.output_deps)
        return outputs
