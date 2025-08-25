#!/usr/bin/env python3
import os
import pytest
import shutil
import tempfile
from yaht.config_processing import read_config_file


def gen_config_file(config):
    """Setup a temp directory to run the tests in"""
    temp_dir = tempfile.mkdtemp()
    config_fname = os.path.join(temp_dir, "config.yaml")
    with open(config_fname, "w") as f:
        f.write(config)
    return config_fname


def clean_dict(d):
    """
    Recursively remove all keys with values that are None,
    empty collections etc. from a dictionary.
    For easier comparison between generated and expected configs
    """
    if not isinstance(d, (dict, list)):
        return d
    if isinstance(d, list):
        return [v for v in (clean_dict(v) for v in d) if v]
    return {k: v for k, v in ((k, clean_dict(v)) for k, v in d.items()) if v}


def test_process_sources():
    """Test the loading of the structure and process sources"""
    yaml_config = "\n".join(
        [  # Global sources are set as a dictionary
            "SOURCES:",
            '  some_file: "file:example_file"',
            '  another_file: "file:example_file"',
            "some_experiment:",
            "  results: foo",
            "",
            # The sources for each process are set as comma-separated strings
            "  structure:",
            "    foo: some_file",
            "    bar: some_file, another_file",
        ]
    )
    config_fname = gen_config_file(yaml_config)

    config = clean_dict(read_config_file(config_fname))
    expected_config = {
        "sources": {
            "some_file": "file:example_file",
            "another_file": "file:example_file",
        },
        "experiments": {
            "some_experiment": {
                # Each process should be expanded into a dictionary
                "structure": {
                    "foo": {
                        "sources": ["some_file"],
                        "function": "foo",
                        "results": ["foo"],
                    },
                    "bar": {
                        "sources": ["some_file", "another_file"],
                        "function": "bar",
                        "results": ["bar"],
                    },
                },
                "results": ["foo"],
            }
        },
    }
    assert config == expected_config


def test_process_general_settings():
    """Test the loading of the structure and process sources"""
    yaml_config = "\n".join(
        [
            # The settings could be anything
            "SETTINGS:",
            '  setting1: "some_setting"',
            "  another_setting: 12",
            "SOURCES:",
            '  some_file: "file:example_file"',
            "some_experiment:",
            "  results: foo",
            "  structure:",
            "    foo: some_file",
            "    bar: some_file, another_file",
        ]
    )
    config_fname = gen_config_file(yaml_config)

    config = clean_dict(read_config_file(config_fname))
    expected_settings = {
        "setting1": "some_setting",
        "another_setting": 12,
    }
    assert config.get("settings") == expected_settings


def test_multiple_trials():
    """test reading a config that specifies multiple trials"""
    yaml_config = "\n".join(
        [
            "SOURCES:",
            '  some_file: "file:example_file"',
            "some_experiment:",
            "  results: foo",
            "",
            "  structure:",
            "    foo: some_file",
            "",
            # Each trial is specified as a dictionary of parameters
            "  trials:",
            "    trial1:",
            "      p1: 3",
            "    trial2:",
            "      p1: -1",
        ]
    )
    config_fname = gen_config_file(yaml_config)

    config = clean_dict(read_config_file(config_fname))
    expected_config = {
        "sources": {"some_file": "file:example_file"},
        "experiments": {
            "some_experiment": {
                "structure": {
                    "foo": {
                        "sources": ["some_file"],
                        "function": "foo",
                        "results": ["foo"],
                    }
                },
                "results": ["foo"],
                # The experiment will be carried out with the same structure
                # for each set of parameters specified in the trials
                "trials": {
                    "trial1": {"p1": 3},
                    "trial2": {"p1": -1},
                },
            }
        },
    }
    assert config == expected_config


def test_parameters():
    """test reading a config that specifies global parameters"""
    yaml_config = "\n".join(
        [
            "SOURCES:",
            '  some_file: "file:example_file"',
            "some_experiment:",
            "  results: foo",
            "",
            "  structure:",
            "    foo: some_file",
            "",
            # The global parameters are also specified as a dictionary of parameters
            "  parameters:",
            "    p1: 12",
        ]
    )
    config_fname = gen_config_file(yaml_config)

    config = clean_dict(read_config_file(config_fname))
    expected_config = {
        "sources": {"some_file": "file:example_file"},
        "experiments": {
            "some_experiment": {
                "structure": {
                    "foo": {
                        "sources": ["some_file"],
                        "function": "foo",
                        "results": ["foo"],
                    }
                },
                "results": ["foo"],
                # These are global parameters
                # that apply to all trials in an experiment
                "parameters": {"p1": 12},
            }
        },
    }
    assert config == expected_config


def test_setting_process_results():
    """Test naming or specifying multiple results of a process"""
    yaml_config = "\n".join(
        [
            "SOURCES:",
            '  some_file: "file:example_file"',
            "some_experiment:",
            "  results: foo",
            "",
            # An arrow after the sources of a proc specifies a list of result names
            "  structure:",
            "    foo: some_file -> foo_result",
            "    bar: some_file -> bar_one, bar_two",
        ]
    )
    config_fname = gen_config_file(yaml_config)

    config = clean_dict(read_config_file(config_fname))
    expected_config = {
        "sources": {"some_file": "file:example_file"},
        "experiments": {
            "some_experiment": {
                # The results of each process should now be specified
                "structure": {
                    "foo": {
                        "sources": ["some_file"],
                        "results": ["foo_result"],
                        "function": "foo",
                    },
                    "bar": {
                        "sources": ["some_file"],
                        "results": ["bar_one", "bar_two"],
                        "function": "bar",
                    },
                },
                "results": ["foo"],
            }
        },
    }
    assert config == expected_config


def test_specifying_global_results():
    """Test specifying the global results of the experiment"""
    yaml_config = "\n".join(
        [
            "SOURCES:",
            '  some_file: "file:example_file"',
            "some_experiment:",
            # Global results are set as a string seperated by commas
            "  results: foo, bar_two",
            "",
            "  structure:",
            "    foo: some_file",
            "    bar: some_file -> bar_one, bar_two",
        ]
    )
    config_fname = gen_config_file(yaml_config)

    config = clean_dict(read_config_file(config_fname))
    expected_config = {
        "sources": {"some_file": "file:example_file"},
        "experiments": {
            "some_experiment": {
                "structure": {
                    "foo": {
                        "sources": ["some_file"],
                        "function": "foo",
                        "results": ["foo"],
                    },
                    "bar": {
                        "sources": ["some_file"],
                        "results": ["bar_one", "bar_two"],
                        "function": "bar",
                    },
                },
                # The global results of the experiment should be a list of two
                "results": ["foo", "bar_two"],
            }
        },
    }
    assert config == expected_config


def test_setting_process_functions():
    """Test overriding the function that a process represents"""
    yaml_config = "\n".join(
        [
            "SOURCES:",
            '  some_file: "file:example_file"',
            "some_experiment:",
            "  results: foo",
            "",
            "  structure:",
            # A proc's function is overriden with an arrow in the dict key
            "    foo <- bar: some_file",
        ]
    )
    config_fname = gen_config_file(yaml_config)

    config = clean_dict(read_config_file(config_fname))
    expected_config = {
        "sources": {"some_file": "file:example_file"},
        "experiments": {
            "some_experiment": {
                # The function of the process should now be specified
                "structure": {
                    "foo": {
                        "sources": ["some_file"],
                        "function": "bar",
                        "results": ["foo"],
                    },
                },
                "results": ["foo"],
            }
        },
    }
    assert config == expected_config


def test_empty_sources():
    """Test specifying empty sources / no sources"""
    yaml_config = "\n".join(
        [
            "some_experiment:",
            "  results: foo",
            "",
            "  structure:",
            # A non-source is given an underscore
            "    foo: _",
            # Giving it alongside another source shouldn't break anything
            "    bar: _, foo, _",
        ]
    )
    config_fname = gen_config_file(yaml_config)

    config = clean_dict(read_config_file(config_fname))
    expected_config = {
        "experiments": {
            "some_experiment": {
                "structure": {
                    "foo": {
                        # As the sources is an empty list, clean_dict should remove it
                        # "sources": [],
                        "function": "foo",
                        "results": ["foo"],
                    },
                    "bar": {
                        # The other process should have only one source
                        "sources": ["foo"],
                        "function": "bar",
                        "results": ["bar"],
                    },
                },
                "results": ["foo"],
            }
        },
    }
    assert config == expected_config
