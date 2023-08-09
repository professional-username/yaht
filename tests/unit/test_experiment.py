#!/usr/bin/env python3
from yaht.processes import register_process
from yaht.experiment import Experiment


# Example function to be used to check outputs etc
@register_process
def add_two_and_custom(x, y, custom="custom"):
    return "%s_%s_%s" % (x, y, custom)


# Mock Laboratory with basic necessary functionality for testing
class MockLaboratory:
    def __init__(self):
        self.data = {}
        self.metadata = {}

    def get_data_by_fname(self, fname):
        return "FILE-%s" % fname

    def get_data(self, key):
        return self.data[key]

    def set_data(self, key, data, metadata=None):
        self.data[key] = data
        self.metadata[key] = metadata

    def check_data(self, key):
        return key in self.data


def test_control_only_trial():
    """Test running a simple experiment with a single trial"""
    config = {
        "inputs": ["input-1", "input-2"],
        "structure": {"add_two_and_custom": ["inputs.0", "inputs.1"]},
        "outputs": ["add_two_and_custom"],
    }
    exp = Experiment(config, MockLaboratory())

    exp.run_trials()
    outputs = exp.get_outputs()

    assert outputs == {"control": ["input-1_input-2_custom"]}


def test_reading_input_from_files():
    """Test reading inputs from the parent Laboratory's files"""
    config = {
        "inputs": ["input-1", "file:input-2"],
        "structure": {"add_two_and_custom": ["inputs.0", "inputs.1"]},
        "outputs": ["add_two_and_custom"],
    }
    exp = Experiment(config, MockLaboratory())

    exp.run_trials()
    outputs = exp.get_outputs()

    assert outputs == {"control": ["input-1_FILE-input-2_custom"]}


def test_only_run_needed_processes():
    """
    Test that if data exists in the parent laboratory,
    the relevant methods are not run
    """
    config = {
        "inputs": ["input-1", "input-2"],
        "structure": {"add_two_and_custom": ["inputs.0", "inputs.1"]},
        "outputs": ["add_two_and_custom"],
    }
    lab = MockLaboratory()
    exp = Experiment(config, lab)

    # Run the trials, change the data, run again and check data is unchanged
    exp.run_trials()
    outputs = exp.get_outputs()
    k = list(lab.data.keys())[0]
    lab.data[k] = "fake_data"
    exp.run_trials()
    outputs = exp.get_outputs()

    assert outputs == {"control": ["fake_data"]}


def test_multiple_trials():
    """Test that we can run different trials with different parameters"""
    config = {
        "inputs": ["input-1", "input-2"],
        "structure": {"add_two_and_custom": ["inputs.0", "inputs.1"]},
        "outputs": ["add_two_and_custom"],
        "trials": {
            "trial1": {"custom": "t1"},
            "trial2": {"custom": "t2"},
        },
    }
    exp = Experiment(config, MockLaboratory())

    exp.run_trials()
    outputs = exp.get_outputs()

    assert outputs == {
        "control": ["input-1_input-2_custom"],
        "trial1": ["input-1_input-2_t1"],
        "trial2": ["input-1_input-2_t2"],
    }


def test_global_parameters():
    """Test applying parameters to all trials unless overriden"""
    config = {
        "inputs": ["input-1", "input-2"],
        "structure": {"add_two_and_custom": ["inputs.0", "inputs.1"]},
        "outputs": ["add_two_and_custom"],
        "trials": {
            "trial1": {"random_param": "param"},
            "trial2": {"custom": "t2"},
        },
        "params": {"custom": "default"},
    }
    exp = Experiment(config, MockLaboratory())

    exp.run_trials()
    outputs = exp.get_outputs()

    assert outputs == {
        "control": ["input-1_input-2_default"],
        "trial1": ["input-1_input-2_default"],
        "trial2": ["input-1_input-2_t2"],
    }


def test_metadata_generation():
    """Test the every method run generates the correct metadata"""
    config = {
        "inputs": ["input-1", "input-2"],
        "structure": {"add_two_and_custom": ["inputs.0", "inputs.1"]},
        "outputs": ["add_two_and_custom"],
    }
    parent_lab = MockLaboratory()
    exp = Experiment(config, parent_lab)

    exp.run_trials()
    outputs = exp.get_outputs()

    assert (
        list(parent_lab.metadata.values())[0]["source"] == "control.add_two_and_custom"
    )
