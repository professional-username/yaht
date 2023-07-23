#!/usr/bin/env python3
import yaht.experiment
from yaht.experiment import Experiment


def test_create_experiment(mocker):
    """
    Test that creating an experiment passes the right arguments
    to the Trial and CacheManager
    """
    mock_trial = mocker.patch("yaht.experiment.Trial", autospec=True)
    mock_cache_manager = mocker.patch("yaht.experiment.CacheManager", autospec=True)
    config = {
        "inputs": ["some_input"],
        "outputs": ["some_output"],
        "structure": "someStructure",
        "cache_dir": "someCacheDir",
    }

    # Create the experiment and check the mocks were called correctly
    exp = Experiment(config)
    mock_trial.assert_called_with(
        exp,
        {
            "structure": "someStructure",
            "parameters": {},
        },
    )
    mock_cache_manager.assert_called_with("someCacheDir")


def test_create_multi_trial_experiment(mocker):
    """
    Test that passing including 'trials' in the config
    results in multiple trials with the right parameters
    """
    mock_trial = mocker.patch("yaht.experiment.Trial", autospec=True)
    mocker.patch("yaht.experiment.CacheManager", autospec=True)
    config = {
        "inputs": ["test_input"],
        "outputs": ["add_foo"],
        "cache_dir": "someCacheDir",
        "structure": "someStructure",
        "trials": {
            "trial1": "some_parameters",
            "trial2": "some_other_parameters",
        },
    }

    # Create the experiment and check trial was called with both sets of params,
    # as well as a control
    exp = Experiment(config)
    mock_trial.assert_any_call(exp, {"structure": "someStructure", "parameters": {}})
    mock_trial.assert_any_call(
        exp,
        {"structure": "someStructure", "parameters": "some_parameters"},
    )
    mock_trial.assert_any_call(
        exp,
        {"structure": "someStructure", "parameters": "some_other_parameters"},
    )


# class MockTrial:
#     def __init__(self, *args, **kwargs):
#         # Store the inputs in instance variables for later verification:
#         self.args = args
#         self.kwargs = kwargs

# class MockCacheManager:
#     def __init__(self, *args, **kwargs):
#         # Store the inputs in instance variables for later verification:
#         self.args = args
#         self.kwargs = kwargs


# def test_get_input():
#     pass


# def test_get_data():
#     pass


# def test_set_data():
#     pass


# def test_check_data():
#     pass
