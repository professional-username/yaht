#!/usr/bin/env python3
import pytest
import pandas as pd
from yaht.structure import generate_laboratory_structure


@pytest.fixture
def mock_all_procs(mocker):
    def mock_get_process(proc_name):
        return lambda x: "%s_%s" % (x, proc_name)

    mocker.patch("yaht.structure.get_process", mock_get_process)


def test_simple_data_input(mock_all_procs):
    """Test the most bare essential config that reads input from a given hash"""
    config = {
        "experiments": {
            "exp1": {
                "inputs": ["hash:DATA_HASH"],
                "structure": {
                    "foo": ["inputs.0"],
                },
                "outputs": ["foo"],
            }
        },
    }

    # Generate the structure
    structure = generate_laboratory_structure(config)
    structure.index = structure["name"]  # For easier testing

    # There should be a single row for a single process
    assert type(structure) == pd.DataFrame
    assert len(structure) == 1
    # The process should have the correct assigned experiment
    assert structure.loc["foo", "experiment"] == "exp1"
    # The input hash of the single process should be correct
    assert structure.loc["foo", "dep_hashes"] == ["DATA_HASH"]


def test_simple_file_input(mock_all_procs):
    """Test the most bare essential config that reads input from a file"""
    config = {
        "input_files": {"EXAMPLE_FILE": "FILE_HASH"},
        "experiments": {
            "exp1": {
                "inputs": ["file:EXAMPLE_FILE"],
                "structure": {
                    "foo": ["inputs.0"],
                },
                "outputs": ["foo"],
            }
        },
    }

    # Generate the structure
    structure = generate_laboratory_structure(config)
    structure.index = structure["name"]  # For easier testing

    # The input hash of the single process should be correct
    assert structure.loc["foo", "dep_hashes"] == ["FILE_HASH"]


def test_multiple_experiments(mock_all_procs):
    """Test setting up multiple experiments"""
    config = {
        "experiments": {
            "exp1": {
                "inputs": ["hash:DATA_HASH"],
                "structure": {
                    "foo": ["inputs.0"],
                },
                "outputs": ["foo"],
            },
            "exp2": {
                "inputs": ["hash:ANOTHER_DATA_HASH"],
                "structure": {
                    "foo": ["inputs.0"],
                    "bar": ["foo"],
                },
                "outputs": ["bar"],
            },
        },
    }

    # Generate the structure
    structure = generate_laboratory_structure(config)
    structure.set_index(["experiment", "name"], inplace=True)  # For easier testing

    # There should be three processes
    assert type(structure) == pd.DataFrame
    assert len(structure) == 3
    # Check that every process has the correct dependency hashes
    assert structure.loc[("exp1", "foo"), "dep_hashes"] == ["DATA_HASH"]
    assert structure.loc[("exp2", "foo"), "dep_hashes"] == ["ANOTHER_DATA_HASH"]
    assert structure.loc[("exp2", "bar"), "dep_hashes"] == [
        structure.loc[("exp2", "foo"), "hash"]
    ]
