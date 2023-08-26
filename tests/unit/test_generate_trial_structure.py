#!/usr/bin/env python3
import pytest
from yaht.processes import register_process
from yaht.trial import generate_trial_structure


@pytest.fixture
def mock_all_procs(mocker):
    def mock_get_process(proc_name):
        return lambda x: "%s_%s" % (x, proc_name)

    mocker.patch("yaht.trial.get_process", mock_get_process)


@pytest.fixture
def simple_proc():
    # Create a test process with a parameter that can be set
    @register_process
    def foobar(x):
        return x

    yield foobar


@pytest.fixture
def proc_with_param():
    # Create a test process with a parameter that can be set
    @register_process
    def add_value(x, value=0):
        return x + value

    yield add_value


def test_single_process_structure(simple_proc):
    """Test the most basic structure"""
    config = {
        "inputs": ["INPUT_HASH"],
        "structure": {
            "foobar": ["inputs.0"],
        },
    }

    structure = generate_trial_structure(config)

    # There should be a single row for a single process
    assert len(structure) == 1
    # The hash just has to exist
    hash_key = structure["hash"].item()
    # The other values should be as follows:
    assert structure.iloc[0].to_dict() == {
        "hash": hash_key,
        "name": "foobar",
        "order": 0,
        "function": simple_proc,
        "params": {},
        "deps": ["inputs.0"],
        "dep_hashes": ["INPUT_HASH"],
    }


def test_process_web(mock_all_procs):
    """Test a multi-process web config"""
    config = {
        "inputs": ["INPUT_ONE", "INPUT_TWO"],
        "structure": {
            "foo": ["foobar.1", "bar"],
            "bar": ["foobar.0"],
            "foobar": ["inputs.1"],
        },
    }

    # Generate the structure
    structure = generate_trial_structure(config)
    structure.index = structure["name"]  # For easier testing

    # Check that the hashes match up correctly
    assert structure.loc["foo", "deps"] == ["foobar.1", "bar"]
    assert structure.loc["foo", "dep_hashes"] == [
        structure.loc["foobar", "hash"] + ".1",
        structure.loc["bar", "hash"],
    ]
    assert structure.loc["foobar", "dep_hashes"] == ["INPUT_TWO"]
    # Check that the order is correct
    assert structure.loc["foobar", "order"] == 0
    assert structure.loc["bar", "order"] == 1
    assert structure.loc["foo", "order"] == 2


def test_overwrite_methods(simple_proc):
    """Test overwriting the method in a function web"""
    config = {
        "inputs": ["INPUT_HASH"],
        "structure": {
            "f1 <- foobar": ["inputs.0"],
            "f2 <- foobar": ["f1"],
        },
    }

    # Generate the structure
    structure = generate_trial_structure(config)
    structure.index = structure["name"]  # For easier testing

    # The two different procs should have the same function
    assert structure.loc["f1", "function"] == simple_proc
    assert structure.loc["f2", "function"] == simple_proc


def test_set_params(proc_with_param):
    """Test passing parameters to some processes"""

    config = {
        "inputs": ["INPUT_HASH"],
        "structure": {
            "add_value": ["inputs.0"],
        },
        "parameters": {
            "value": 2,
        },
    }

    # Generate the structure
    structure = generate_trial_structure(config)
    structure.index = structure["name"]  # For easier testing

    # Check that the parameter is set correctly
    assert structure.loc["add_value", "params"] == {"value": 2}


def test_setting_specific_process_parameters(proc_with_param):
    """Test setting parameters for only specific processes"""
    config = {
        "inputs": ["INPUT_HASH"],
        "structure": {
            "add_value": ["inputs.0"],
        },
        "parameters": {
            "value": "WRONG",
            "add_value.value": "CORRECT",
        },
    }

    # Generate the structure
    structure = generate_trial_structure(config)
    structure.index = structure["name"]  # For easier testing

    # The specificly set parameter is the one that should be applied
    assert structure.loc["add_value", "params"] == {"value": "CORRECT"}


def test_setting_methods_as_parameters(simple_proc):
    """Test replacing structural components with parameters"""
    config = {
        "inputs": ["INPUT_HASH"],
        "structure": {
            "f1": ["inputs.0"],
            "foobar": ["fake_input"],
        },
        "parameters": {
            "f1 <- foobar": ["inputs.0"],
            "foobar <- foobar": ["f1"],
        },
    }

    # Generate the structure
    structure = generate_trial_structure(config)
    structure.index = structure["name"]  # For easier testing

    # Check that both the functions are correct
    assert structure.loc["f1", "function"] == simple_proc
    assert structure.loc["foobar", "function"] == simple_proc
    # Check that the inputs are overridden correctly
    assert structure.loc["foobar", "deps"] == ["f1"]
    assert structure.loc["foobar", "dep_hashes"] == [structure.loc["f1", "hash"]]
