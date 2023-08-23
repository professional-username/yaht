#!/usr/bin/env python3
import os
import pytest
import tempfile
import pandas as pd
from yaht.cache_management import CacheManager
from yaht.laboratory import Laboratory


class MockDataExporter:
    """A mock data exporter that records any data 'exported'"""

    def __init__(self):
        self.data = []

    def export_data(self, data):
        self.data.append(data)


# Setup a temp directory to run the tests in
@pytest.fixture
def cache_dir():
    new_dir = tempfile.mkdtemp()
    yield os.path.join(new_dir, "cache")
    # shutil.rmtree(new_dir)


# Override the get_process method
@pytest.fixture
def mock_processes(mocker):
    def mock_get_process(proc_name):
        return lambda x: "%s_%s" % (x, proc_name)

    mocker.patch("yaht.trial.get_process", mock_get_process)


# A base lab config to run and tinker with
@pytest.fixture
def base_lab_config(cache_dir):
    config = {
        "cache_dir": cache_dir,
        "experiments": {
            "exp1": {
                "inputs": ["INPUT"],
                "outputs": ["p1"],
                "structure": {"p1": ["inputs.0"]},
            }
        },
    }
    yield config


def test_base_config(mock_processes, base_lab_config):
    """Test that running a simple config exports the correct data"""
    data_exporter = MockDataExporter()
    lab = Laboratory(base_lab_config, data_exporter)

    lab.run_experiments()
    lab.export_experiment_results()

    # Output should be a dataframe
    outputs = data_exporter.data[0]

    expected_outputs = pd.DataFrame(columns=["data", "experiment", "trial", "process"])
    expected_outputs["experiment"] = ["exp1"]
    expected_outputs["trial"] = ["control"]
    expected_outputs["process"] = ["p1"]
    expected_outputs["data"] = ["INPUT_p1"]

    assert outputs.equals(expected_outputs)


def test_reading_input_data_from_file(mock_processes, base_lab_config, cache_dir):
    """
    Test that we can write data to a file in the cache
    and use it as input to the experiment
    """
    # Write some data to the cache
    external_cache_manager = CacheManager(cache_dir)
    external_cache_manager.send_data(
        key="inputFile",
        data="FILE_INPUT_DATA",
        metadata={"filename": "inputFile"},
    )

    # Update the config to use the file as input
    updated_config = base_lab_config
    updated_config["experiments"]["exp1"]["inputs"] = ["file:inputFile"]

    # Run the lab with the new config
    data_exporter = MockDataExporter()
    lab = Laboratory(updated_config, data_exporter)
    lab.run_experiments()
    lab.export_experiment_results()
    outputs = data_exporter.data[0]

    assert outputs["data"].values == ["FILE_INPUT_DATA_p1"]


def test_multiple_experiments():
    # Necessary?
    pass


def test_export_outputs_metadata():
    """Test exporting the metadata for the laboratory's outputs"""


def test_export_input_metadata():
    # ??
    pass


def test_export_all_metadata():
    pass
