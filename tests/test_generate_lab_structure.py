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
        "source_hashes": {"in": "DATA_HASH"},
        "experiments": {
            "exp1": {
                "structure": {
                    "foo": {"sources": ["in"]},
                },
                "results": ["foo"],
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
    assert structure.loc["foo", "source_hashes"] == ["DATA_HASH"]


def test_multiple_experiments(mock_all_procs):
    """Test setting up multiple experiments"""
    config = {
        "source_hashes": {
            "input1": "DATA_HASH",
            "input2": "ANOTHER_DATA_HASH",
        },
        "experiments": {
            "exp1": {
                "structure": {
                    "foo": {"sources": ["input1"]},
                },
                "results": ["foo"],
            },
            "exp2": {
                "structure": {
                    "foo": {"sources": ["input2"]},
                    "bar": {"sources": ["foo"]},
                },
                "results": ["bar"],
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
    assert structure.loc[("exp1", "foo"), "source_hashes"] == ["DATA_HASH"]
    assert structure.loc[("exp2", "foo"), "source_hashes"] == ["ANOTHER_DATA_HASH"]
    assert (
        structure.loc[("exp2", "bar"), "source_hashes"]
        == [structure.loc[("exp2", "foo"), "result_hashes"]][0]
    )
