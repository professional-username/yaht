#!/usr/bin/env python3
import yaml
from yaht.experiment import Experiment
from yaht.processes import register_process

EXAMPLE_CONFIG = """
Experiment:
  inputs: [ "input" ]
  outputs: [ f1 ]
  structure:
    f1: [ inputs ]
"""


# Example functions
@register_process
def f1(x):
    y = x.upper()
    return y


@register_process
def f2(x):
    y = x[0].lower() + x[1:]
    return y


@register_process
def f3(a, b):
    y = a + b
    return y


def test_run_functions():
    """
    Test that we can create an experiment
    and that it will run registered function
    """
    # Example config that runs "input" through the function f1, then f2
    example_config = [
        'inputs: [ "input" ]',
        "outputs: [ f2 ]",
        "structure:",
        "  f1: [ inputs.0 ]",
        "  f2: [ f1 ]",
    ]
    example_config = yaml.safe_load("\n".join(example_config))

    experiment = Experiment(example_config)
    experiment.run()

    output = experiment.get_outputs()
    assert output == ["iNPUT"]


def test_function_web():
    """Test that we can run functions in a more complicated web"""
    # Example config that runs some example functions in a web
    example_config = [
        'inputs: [ "one", "two" ]',
        "outputs: [ f3 ]",
        "structure:",
        "  f3: [ f2, inputs.1 ]",
        "  f2: [ f1 ]",
        "  f1: [ inputs.0 ]",
    ]
    example_config = yaml.safe_load("\n".join(example_config))

    # Experiment should run "one" through f1, then f2
    # then combine that with "two" in f3
    experiment = Experiment(example_config)
    experiment.run()

    output = experiment.get_outputs()
    assert output == ["oNEtwo"]
