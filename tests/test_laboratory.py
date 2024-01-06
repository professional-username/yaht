#!/usr/bin/env python3
import os
import shutil
import pytest
import tempfile
import pandas as pd
import yaht.cache_management as CM
from yaht.laboratory import Laboratory


@pytest.fixture
def mock_all_procs(mocker):
    def mock_get_process(proc_name):
        return lambda x: "%s_%s" % (x, proc_name)

    mocker.patch("yaht.structure.get_process", mock_get_process)


@pytest.fixture
def mock_config():
    # Create a mock cache
    new_dir = tempfile.mkdtemp()
    cache_dir = os.path.join(new_dir, "cache")
    CM.store_cache_data(cache_dir, "example_key", "EXAMPLE_DATA")
    source_fname = (
        CM.load_cache_metadata(cache_dir)
        .set_index("hash")
        .loc["example_key", "filename"]
    )

    config = {
        "settings": {
            "lab_name": "some_lab_name",
            "cache_dir": cache_dir,
        },
        "sources": {
            "some_data": "file:" + source_fname,
        },
        "experiments": {
            "some_experiment": {
                "structure": {
                    "foo": {
                        "sources": ["some_data"],
                        "function": "foo",
                    },
                    "bar": {
                        "sources": ["foo"],
                        "function": "bar",
                        "results": ["bar_result"],
                    },
                },
                "results": ["bar_result"],
            }
        },
    }
    yield config
    shutil.rmtree(new_dir)


def test_lab_run_experiments(mock_config, mock_all_procs):
    """We should be able to run the above experiment and return the results"""
    lab = Laboratory(mock_config)
    lab.run_experiments()
    results = lab.get_results()
    # The results should be a dataframe of data
    assert type(results) == pd.DataFrame
    assert len(results) == 1
    assert results["experiment"][0] == "some_experiment"
    assert results["trial"][0] == "control"
    assert results["process"][0] == "bar"
    assert results["name"][0] == "bar_result"
    assert results["value"][0] == "EXAMPLE_DATA_foo_bar"
    assert results["hash"][0]  # We don't know what the hash is but it should be there


def test_lab_metadata_generation(mock_config, mock_all_procs):
    """Running experiments should generate all sorts of metadata"""
    lab = Laboratory(mock_config)
    lab.run_experiments()
    cache_dir = mock_config["settings"]["cache_dir"]
    cached_metadata = CM.load_cache_metadata(cache_dir)

    # Check that things like source and filename are set correctly
    assert "some_lab_name/some_experiment.control.foo" in list(
        cached_metadata["source"]
    )
    assert "some_lab_name/some_experiment.control.bar" in list(
        cached_metadata["source"]
    )
    # Check that the filename has the right components at least
    assert "some_lab_name" in cached_metadata["filename"][0]
    assert "some_experiment" in cached_metadata["filename"][0]
    assert "control" in cached_metadata["filename"][0]