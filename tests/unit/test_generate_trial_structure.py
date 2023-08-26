#!/usr/bin/env python3
import pytest
from yaht.trial import generate_trial_structure


@pytest.fixture
def mock_processes(mocker):
    def mock_get_process(proc_name):
        return lambda x: "%s_%s" % (x, proc_name)

    mocker.patch("yaht.trial.get_process", mock_get_process)


def test_single_process_structure(mock_processes):
    """Test the most basic structure"""
    config = {
        "inputs": ["INPUT_HASH"],
        "structure": {
            "foo": ["inputs.0"],
        },
    }

    structure = generate_trial_structure(config)

    assert len(structure) == 1
    assert "hash" in structure.columns
    assert structure["deps"].values[0] == ["inputs.0"]
    assert structure["dep_hashes"].values[0] == ["INPUT_HASH"]
    assert structure["name"].values[0] == "foo"
    assert structure["function"].values[0]("test") == "test_foo"
    assert structure["parameters"].values[0] == {}
    assert structure["order"].values[0] == 0
