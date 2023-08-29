#!/usr/bin/env python3
import pytest
import pandas as pd
from yaht.processes import register_process
from yaht.experiment import generate_experiment_structure


@pytest.fixture
def mock_all_procs(mocker):
    def mock_get_process(proc_name):
        return lambda x: "%s_%s" % (x, proc_name)

    mocker.patch("yaht.trial.get_process", mock_get_process)


@pytest.fixture
def proc_with_param():
    # Create a test process with a parameter that can be set
    @register_process
    def add_value(x, value=0):
        return x + value

    yield add_value


def test_control_only_trial(mock_all_procs):
    """Test a simple experiment with a single trial"""
    config = {
        "inputs": ["INPUT_HASH"],
        "structure": {
            "foo": ["inputs.0"],
            "bar": ["foo"],
        },
        "outputs": ["bar"],
    }

    # Generate the structure
    structure = generate_experiment_structure(config)
    structure.index = structure["name"]  # For easier testing

    # There should be a single row for a single process
    assert type(structure) == pd.DataFrame
    assert len(structure) == 2
    # These are columns specific to the experiment config
    assert structure.loc["foo", "trial"] == "control"
    assert structure.loc["bar", "trial"] == "control"
    assert structure.loc["foo", "output"] == False
    assert structure.loc["bar", "output"] == True


def test_multiple_trials(proc_with_param):
    """Test that passing some parameters generates an extra trial"""
    config = {
        "inputs": ["INPUT_HASH"],
        "structure": {
            "add_value": ["inputs.0"],
        },
        "outputs": ["add_value"],
        "trials": {
            "trial1": {"value": "ONE"},
            "trial2": {"value": "TWO"},
        },
    }

    # Generate the structure
    structure = generate_experiment_structure(config)
    structure.set_index(["trial", "name"], inplace=True)  # For easier testing

    # There should be 3 copies of the same process with different parameters
    assert len(structure) == 3
    assert structure.loc[("control", "add_value"), "params"] == {}
    assert structure.loc[("trial1", "add_value"), "params"] == {"value": "ONE"}
    assert structure.loc[("trial2", "add_value"), "params"] == {"value": "TWO"}
    # They should all be marked as output
    assert structure.loc[("control", "add_value"), "output"] == True
    assert structure.loc[("trial1", "add_value"), "output"] == True
    assert structure.loc[("trial2", "add_value"), "output"] == True


def test_global_parameters():
    """Test setting parameters that apply to all processes"""
    config = {
        "inputs": ["INPUT_HASH"],
        "structure": {
            "add_value": ["inputs.0"],
        },
        "outputs": ["add_value"],
        "parameters": {"value": "GLOBAL"},
        "trials": {
            "trial1": {"some_other_value": "ONE"},
            "trial2": {"value": "TWO"},
        },
    }

    # Generate the structure
    structure = generate_experiment_structure(config)
    structure.set_index(["trial", "name"], inplace=True)  # For easier testing

    # The global parameter should apply to everything that isn't set by trial configs
    assert structure.loc[("control", "add_value"), "params"] == {"value": "GLOBAL"}
    assert structure.loc[("trial1", "add_value"), "params"] == {"value": "GLOBAL"}
    assert structure.loc[("trial2", "add_value"), "params"] == {"value": "TWO"}
