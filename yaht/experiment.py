import pandas as pd
from itertools import product
from yaht.trial import Trial, generate_trial_structure


class Experiment:
    def __init__(self, config, parent_laboratory):
        self.input_names = config["inputs"]
        self.output_proc_names = config["outputs"]

        self.parent_laboratory = parent_laboratory
        trial_configs = self.extract_trial_configs(config)
        self.trials = {t: Trial(self, trial_configs[t]) for t in trial_configs}

        self.currently_running_trial = ""

    def extract_trial_configs(self, config):
        """Convert the experiment config into several trial configs"""
        # Ensure that the config has a "trials" section with at least a 'control'
        if "trials" not in config:
            config["trials"] = {}
        config["trials"]["control"] = {}

        # Get global parameters if there are any
        global_params = config["params"] if "params" in config else {}

        # Assemble the trial configs
        trial_configs = {}
        structure = config["structure"]
        for trial_name in config["trials"]:
            trial_params = global_params | config["trials"][trial_name]
            new_trial_config = {"structure": structure, "parameters": trial_params}
            trial_configs[trial_name] = new_trial_config

        return trial_configs

    def run_trials(self):
        """Run each trial one by one"""
        for trial_name in self.trials:
            self.currently_running_trial = trial_name  # Track the current trial
            self.trials[trial_name].run()

    def get_input(self, input_index):
        """
        If input is a file, pass the call to the parent laboratory,
        otherwise return the input as given
        """
        input_index = int(input_index)
        input_name = self.input_names[input_index]
        # If the input is a file, load the file
        if str(input_name).startswith("file:"):
            input_name = input_name[5:]
            input_data = self.parent_laboratory.get_data_by_fname(input_name)
        # Otherwise, the input provided in the config is taken literally
        else:
            input_data = input_name

        return input_data

    def get_outputs(self):
        """
        Use self.output_names to retrieve output data from the parent lab,
        by getting the relevant data hash from each trial
        """
        outputs = pd.DataFrame(columns=["data", "trial", "process"])
        for trial_name, proc_name in product(self.trials, self.output_proc_names):
            # Retrieve the output
            trial = self.trials[trial_name]
            trial_proc_output_hash = trial.proc_hashes[proc_name]
            trial_proc_output = self.get_data(trial_proc_output_hash)
            # Place it into the output df
            new_row_dict = {
                "data": trial_proc_output,
                "trial": trial_name,
                "process": proc_name,
            }
            new_row = pd.DataFrame([new_row_dict])
            outputs = pd.concat([outputs, new_row], ignore_index=True)

        return outputs

    def get_data(self, data_index):
        """Pass on data calls to the parent laboratory"""
        return self.parent_laboratory.get_data(data_index)

    def set_data(self, data_index, data, metadata={}):
        """Pass on data calls to the parent laboratory"""
        # Update the metadata
        metadata["source"] = (
            "%s.%s" % (self.currently_running_trial, metadata["source"])
            if "source" in metadata
            else self.currently_running_trial
        )

        self.parent_laboratory.set_data(data_index, data, metadata)

    def check_data(self, data_index):
        """Pass on data calls to the parent laboratory"""
        return self.parent_laboratory.check_data(data_index)
