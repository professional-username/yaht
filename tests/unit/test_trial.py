#!/usr/bin/env python3
import yaml
from unittest.mock import MagicMock
from yaht.processes import register_process
from yaht.trial import Trial


# Example function creation which adds the function name to the passed string
# to easily show which functions ran on which inputs in which order
def new_mock_process(name):
    proc = lambda input_string: "%s_%s" % (input_string, name)
    proc.__name__ = name
    return register_process(proc)


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
    config = [
        'inputs: [ "input" ]',
        "outputs: [ f1 ]",
        "structure:",
        "  f1: [ inputs.0 ]",
    ]
    config = yaml.safe_load("\n".join(config))

    # Setup mocks
    f1 = new_mock_process("f1")
    exp = MockExperiment()

    trial = Trial(exp, config)
    trial.run()

    # Assert the right external functions were called with the right values
    assert trial.get_output() == ["input_0_f1"]
