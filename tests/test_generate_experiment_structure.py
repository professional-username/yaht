#!/usr/bin/env python3
import pytest
import pandas as pd
from yaht.processes import register_process
from yaht.structure import generate_experiment_structure


@pytest.fixture
def mock_all_procs(mocker):
    def mock_get_process(proc_name):
        return lambda x: "%s_%s" % (x, proc_name)

    mocker.patch("yaht.structure.get_process", mock_get_process)


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
        "source_hashes": {"in": "INPUT_HASH"},
        "structure": {
            "foo": {"sources": ["in"]},
            "bar": {"sources": ["foo"]},
        },
        "results": ["bar"],
    }

    # Generate the structure
    structure = generate_experiment_structure(config)
    structure.index = structure["name"]  # For easier testing

    # There should be two rows for two processes
    assert type(structure) == pd.DataFrame
    assert len(structure) == 2
    # These are columns specific to the experiment config
    assert structure.loc["foo", "trial"] == "control"
    assert structure.loc["bar", "trial"] == "control"
    assert structure.loc["foo", "results"] == [False]
    assert structure.loc["bar", "results"] == [True]


def test_multiple_trials(proc_with_param):
    """Test that passing some parameters generates an extra trial"""
    config = {
        "source_hashes": {"in": "INPUT_HASH"},
        "structure": {
            "add_value": {"sources": ["in"]},
        },
        "results": ["add_value"],
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
    # They should all be marked as results
    assert structure.loc[("control", "add_value"), "results"] == [True]
    assert structure.loc[("trial1", "add_value"), "results"] == [True]
    assert structure.loc[("trial2", "add_value"), "results"] == [True]


def test_specific_process_parameter_setting(proc_with_param):
    """Test setting the parameter for a specific process"""
    config = {
        "source_hashes": {"in": "INPUT_HASH"},
        "structure": {
            "add_1": {"sources": ["in"], "function": "add_value"},
            "add_2": {"sources": ["add_1"], "function": "add_value"},
        },
        "results": ["add_2"],
        "trials": {
            "trial1": {"add_2.value": "ONE"},
            "trial2": {"add_2.value": "TWO"},
        },
    }

    # Generate the structure
    structure = generate_experiment_structure(config)
    structure.set_index(["trial", "name"], inplace=True)  # For easier testing

    assert len(structure) == 6
    # There should be 3 copies of the first process with the same params
    assert structure.loc[("control", "add_1"), "params"] == {}
    assert structure.loc[("trial1", "add_1"), "params"] == {}
    assert structure.loc[("trial2", "add_1"), "params"] == {}
    # And different params for the second process
    assert structure.loc[("control", "add_2"), "params"] == {}
    assert structure.loc[("trial1", "add_2"), "params"] == {"value": "ONE"}
    assert structure.loc[("trial2", "add_2"), "params"] == {"value": "TWO"}


def test_global_parameters():
    """Test setting parameters that apply to all processes"""
    config = {
        "source_hashes": {"in": "INPUT_HASH"},
        "structure": {
            "add_value": {"sources": ["in"]},
        },
        "results": ["add_value"],
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


def test_multiple_results(mock_all_procs):
    """Test a simple experiment with a single trial"""
    config = {
        "source_hashes": {"in": "INPUT_HASH"},
        "structure": {
            "foo": {
                "sources": ["in"],
                "results": ["foo_one", "foo_two"],
            },
            "bar": {"sources": ["foo"]},
        },
        "results": ["bar", "foo_two"],
    }

    # Generate the structure
    structure = generate_experiment_structure(config)
    structure.index = structure["name"]  # For easier testing

    # The results from each process can be multiple,
    # and each should be marked as true/false as a result for the experiment
    print(structure)
    assert structure.loc["foo", "results"] == [False, True]
    assert structure.loc["bar", "results"] == [True]
