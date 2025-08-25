#!/usr/bin/env python3
import pytest
import numpy as np
import pandas as pd

# from yaht.result_handling import plot_results
from yaht.outputs import register_output, output_results


@pytest.fixture
def sample_results():
    # Results should look like a dataframe of values
    results = pd.DataFrame()
    results["value"] = [1.0, 2.0, 1.2]
    results["trial"] = ["t1", "t2", "t3"]
    results["name"] = "some_result"
    results["process"] = "some_proc"
    results["experiment"] = "some_experiment"
    results["output"] = None

    yield results


def test_output_results(sample_results):
    """
    Register custom output functions
    and check if they're called with the correct data
    """
    # Record outputted data in a list
    outputted_data = []

    @register_output
    def mock_output(data, metadata):
        outputted_data.append({"data": data, "metadata": metadata})

    # Specify the output function, and process
    sample_results["output"] = "mock_output"
    output_results(sample_results)

    # Check that the expected results were outputted
    expected_data = {
        "data": 2.0,
        "metadata": {
            "trial": "t2",
            "name": "some_result",
            "process": "some_proc",
            "experiment": "some_experiment",
        },
    }
    assert expected_data in outputted_data
