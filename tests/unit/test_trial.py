#!/usr/bin/env python3
from copy import deepcopy
from yaht.processes import register_process
from yaht.trial import Trial


# Example function creation which adds the function name to the passed string
# to easily show which functions ran on which inputs in which order
@register_process
def add_foo(x):
    return "%s_foo" % x


@register_process
def add_foobar(x):
    return "%s_foo" % x, "%s_bar" % x


@register_process
def add_custom(x, custom="custom"):
    return "%s_%s" % (x, custom)


@register_process
def add(x, y):
    return "%s_%s" % (x, y)


# Simplified version of the Experiment class
# to provide an interface for Trial to be tested against
class MockExperiment:
    def __init__(self):
        self.data = {}

    def get_input(self, input_index):
        return "input_%s" % input_index

    def get_data(self, key):
        return self.data.get(key)

    def set_data(self, key, value):
        self.data[key] = value

    def check_data(self, key):
        return key in self.data


def test_single_process_trial():
    """Test a very basic single-process trial config"""
    config = {
        "structure": {
            "add_foo": ["inputs.0"],
        },
    }

    # Run the trial
    trial = Trial(MockExperiment(), config)
    trial.run()

    # Assert the right external functions were called with the right values
    assert trial.get_data(["add_foo"]) == ["input_0_foo"]


def test_process_web():
    """Test a multi-process web config"""
    config = {
        "structure": {
            "add": ["add_foobar.1", "add_foo"],
            "add_foo": ["add_foobar.0"],
            "add_foobar": ["inputs.1"],
        },
    }
    # Run the trial
    trial = Trial(MockExperiment(), config)
    trial.run()

    # Assert the right external functions were called with the right values
    assert trial.get_data(["add_foobar", "add_foo", "add"]) == [
        ("input_1_foo", "input_1_bar"),
        "input_1_foo_foo",
        "input_1_bar_input_1_foo_foo",
    ]


def test_set_params():
    """Test passing parameters to some processes"""
    config = {
        "structure": {
            "add_custom": ["inputs.0"],
        },
        "parameters": {
            "custom": "test",
        },
    }

    # Run the trial
    trial = Trial(MockExperiment(), config)
    trial.run()

    assert trial.get_data(["add_custom"]) == ["input_0_test"]


# def test_overwrite_methods():
#     """Test overwriting the method in a function web"""
#     pass


def test_multiple_process_data_usage():
    """Test that multiple processes can share data in an experiment"""
    base_config = {
        "structure": {
            "add_foo": ["inputs.0"],
            "add_custom": ["add_foo"],
        },
        "parameters": {
            "custom": "base",
        },
    }
    # Two configs, with a different parameter for the second function in each
    config_1 = deepcopy(base_config)
    config_1["parameters"]["custom"] = "test_1"
    config_2 = deepcopy(base_config)
    config_2["parameters"]["custom"] = "test_2"

    # Run each trial with the same parent experiment
    parent_exp = MockExperiment()
    trial1 = Trial(parent_exp, config_1)
    trial2 = Trial(parent_exp, config_2)
    trial1.run()
    trial2.run()

    # There should be only a single result for add_foo, but 2 for add_custom
    assert len(parent_exp.data) == 3


def test_only_run_needed_processes():
    """Test that if data exists for the output of a process, it isn't run"""
    config = {"structure": {"add_foo": ["inputs.0"]}}

    # Run the trial once, change the data, run again to check the data isn't changed
    exp = MockExperiment()
    trial = Trial(exp, config)
    trial.run()
    k = list(exp.data.keys())[0]
    exp.data[k] = "fake_data"
    trial.run()

    assert exp.data[k] == "fake_data"
