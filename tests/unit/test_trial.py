#!/usr/bin/env python3
from yaht.processes import register_process
from yaht.trial import Trial


# Example function creation which adds the function name to the passed string
# to easily show which functions ran on which inputs in which order
def new_mock_processes(names):
    for name in names:
        proc = lambda input_string: "%s_%s" % (input_string, name)
        proc.__name__ = name
        register_process(proc)


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
            "f1": ["inputs.0"],
        },
    }
    # Setup mocks
    new_mock_processes(["f1"])
    exp = MockExperiment()

    # Run the trial
    trial = Trial(exp, config)
    trial.run()

    # Assert the right external functions were called with the right values
    assert trial.get_data(["f1"]) == ["input_0_f1"]
