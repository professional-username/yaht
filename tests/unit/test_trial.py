#!/usr/bin/env python3
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

# def test_multiple_process_data_usage():
#     """Test that multiple processes can share data in an experiment"""
#     pass
