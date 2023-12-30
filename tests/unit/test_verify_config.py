#!/usr/bin/env python3
import pytest
from yaht.config_processing import verify_config


def test_verify_full_config():
    config = {
        "sources": {
            "some_file": "file:example_file",
            "another_file": "file:example_file",
        },
        "experiments": {
            "some_experiment": {
                "structure": {
                    "foo": {
                        "sources": ["some_file"],
                        "function": "foo",
                    },
                    "bar": {
                        "sources": ["some_file", "another_file"],
                        "function": "bar",
                    },
                },
                "results": ["foo", "bar"],
            }
        },
    }
    verify_config(config)


def test_source_mismatch():
    """Detect sources being referenced but_missing"""
    config = {
        "sources": {
            "some_file": "file:example_file",
        },
        "experiments": {
            "some_experiment": {
                "structure": {
                    "foo": {
                        # It's possible to specify a source that doesn't exist
                        "sources": ["MISSING_FILE"],
                        "function": "foo",
                    },
                },
                "results": ["foo"],
            }
        },
    }
    with pytest.raises(ValueError):
        verify_config(config)


def test_result_mismatch():
    """Detect sources referenced within an experiment not existing"""
    config = {
        "sources": {
            "some_file": "file:example_file",
        },
        "experiments": {
            "some_experiment": {
                "structure": {
                    "foo": {
                        "sources": ["some_file"],
                        "function": "foo",
                    },
                },
                # It's possible to specify a result that doesn't exist
                "results": ["MISSING_PROC"],
            }
        },
    }
    with pytest.raises(ValueError):
        verify_config(config)
