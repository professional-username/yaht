#!/usr/bin/env python3
import os
import pytest
import tempfile
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
                "inputs": ["input"],
                "outputs": ["p1"],
                "structure": {"p1": ["inputs.0"]},
            }
        },
    }
    yield config


def test_base_config(mock_processes, base_lab_config):
    data_exporter = MockDataExporter()
    lab = Laboratory(base_lab_config, data_exporter)

    lab.run_experiments()
    lab.export_experiment_results()

    assert data_exporter.data[0] == {"exp1": {"control": ["input_p1"]}}
