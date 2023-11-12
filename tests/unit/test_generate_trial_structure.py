#!/usr/bin/env python3
import pytest
from yaht.processes import register_process
from yaht.structure import generate_trial_structure


@pytest.fixture
def mock_all_procs(mocker):
    def mock_get_process(proc_name):
        return lambda x: "%s_%s" % (x, proc_name)

    mocker.patch("yaht.structure.get_process", mock_get_process)


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
        "source_hashes": {"source_1": "INPUT_HASH"},
        "structure": {
            "foobar": {
                "sources": ["source_1"],
                "results": ["foobar"],
            },
        },
    }

    structure = generate_trial_structure(config)

    # There should be a single row for a single process
    assert len(structure) == 1
    # The hash just has to exist
    hash_key = structure["result_hashes"].item()[0]
    # The other values should be as follows:
    assert structure.iloc[0].to_dict() == {
        # Essential for processing
        "order": 0,
        "function": simple_proc,
        "params": {},
        "source_hashes": ["INPUT_HASH"],
        "result_hashes": [hash_key],
        # Metadata
        "name": "foobar",
        "source_names": ["source_1"],
        "result_names": ["foobar"],
    }


def test_process_web(mock_all_procs):
    """
    Test a multi-process web config,
    with multiple sources or results for different processes
    """
    config = {
        "source_hashes": {
            "source_1": "INPUT_ONE",
            "source_2": "INPUT_TWO",
        },
        "structure": {
            "foo": {
                "sources": ["source_2", "bar.one"],
                # Not specifying results should imply a single result
                # of the same name as the process
                # "results": ["foo"],
            },
            "bar": {
                "sources": ["source_1"],
                "results": ["bar.one", "bar.two"],
            },
            "foobar": {
                "sources": ["foo", "bar.two"],
                "results": ["foobar"],
            },
        },
    }

    # Generate the structure
    structure = generate_trial_structure(config)
    structure.index = structure["name"]  # For easier testing

    # Check that the hashes match up correctly
    assert structure.loc["foobar", "source_names"] == ["foo", "bar.two"]
    assert structure.loc["foobar", "source_hashes"] == [
        structure.loc["foo", "result_hashes"][0],
        structure.loc["bar", "result_hashes"][1],
    ]
    assert structure.loc["bar", "source_hashes"] == ["INPUT_ONE"]
    # Check that the order is correct
    assert structure.loc["bar", "order"] == 0
    assert structure.loc["foo", "order"] == 1
    assert structure.loc["foobar", "order"] == 2


def test_overwrite_methods(simple_proc):
    """Test overwriting the method in a function web"""
    config = {
        "source_hashes": {"main_source": "INPUT_HASH"},
        "structure": {
            "f1": {
                "sources": ["main_source"],
                # The function name is implicitly the same as the process name,
                # But can be specified to be different
                "function": "foobar",
            },
            "f2": {
                "sources": ["f1"],
                "function": "foobar",
            },
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
        "source_hashes": {"main_source": "INPUT_HASH"},
        "structure": {
            "add_value": {
                "sources": ["main_source"],
            },
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
        "source_hashes": {"main_source": "INPUT_HASH"},
        "structure": {
            "add_value": {
                "sources": ["main_source"],
            }
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


def test_setting_structure_as_parameters(simple_proc):
    """Test replacing structural components with parameters"""
    config = {
        "source_hashes": {"main_source": "INPUT_HASH"},
        "structure": {
            "f1": {
                "sources": ["main_source"],
                "results": ["fake_result_one", "fake_result_two"],
            },
            "foobar": {
                "sources": ["fake_input"],
            },
        },
        "parameters": {
            "foobar.SOURCES": ["f1_result"],
            "f1.FUNCTION": "foobar",
            "f1.RESULTS": ["f1_result"],
        },
    }

    # Generate the structure
    structure = generate_trial_structure(config)
    structure.index = structure["name"]  # For easier testing

    # Check that both the functions are correct
    assert structure.loc["f1", "function"] == simple_proc
    assert structure.loc["foobar", "function"] == simple_proc
    # Check that the sources and results are overridden correctly
    assert structure.loc["foobar", "source_names"] == ["f1_result"]
    assert structure.loc["f1", "result_names"] == ["f1_result"]
    assert structure.loc["foobar", "source_hashes"] == [
        structure.loc["f1", "result_hashes"][0]
    ]
