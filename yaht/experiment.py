from yaht.trial import Trial
from yaht.cache_management import CacheManager


class Experiment:
    def __init__(self, config):
        self.cache_manager = CacheManager(config["cache_dir"])
        trial_configs = self.extract_trial_configs(config)
        self.trials = {t: Trial(self, trial_configs[t]) for t in trial_configs}

    def extract_trial_configs(self, config):
        """Convert the experiment config into several trial configs"""
        # Ensure that the config has a "trials" section with at least a 'control'
        if "trials" not in config:
            config["trials"] = {}
        config["trials"]["control"] = {}

        # Assemble the trial configs
        trial_configs = {}
        structure = config["structure"]
        for trial_name in config["trials"]:
            new_trial_config = {
                "structure": structure,
                "parameters": config["trials"][trial_name],
            }
            trial_configs[trial_name] = new_trial_config

        return trial_configs
