#!/usr/bin/env python3
from yaht.processes import get_process


class Trial:
    def __init__(self, parent_experiment, config):
        self.parent_experiment = parent_experiment

        structure = config["structure"]
        # params =
        self.proc_dependencies = structure
        self.proc_functions = {p: get_process(p) for p in structure}
        self.proc_names = [p for p in structure]
        self.proc_hashes = {p: p for p in structure}

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
