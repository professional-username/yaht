#!/usr/bin/env python3
import numpy as np
import pandas as pd
from yaht.result_handling import plot_results


def test_plot_single_value():
    """Test handling scalar results"""
    results = pd.DataFrame()
    results["value"] = [1.0, 2.0, 1.2]
    results["trial"] = ["t1", "t2", "t3"]
    results["name"] = "some_result"
    results["process"] = "some_proc"
    results["experiment"] = "some_experiment"

    result_fig = plot_results(results)
    # There should only be one plot
    result_axes = result_fig.axes
    assert len(result_axes) == 1
    # There should be 3 bars, one for each trial
    assert len(result_axes[0].patches) == 3 + 1
    # TODO: More assertions required


def test_plot_different_values():
    """Test handling scalar results"""
    results = pd.DataFrame()
    results["value"] = [1.0, 2.0, 1.2, 1.5]
    results["trial"] = ["t1", "t2", "t1", "t2"]
    results["name"] = ["res1", "res1", "res2", "res2"]
    results["process"] = "some_proc"
    results["experiment"] = "some_experiment"

    result_fig = plot_results(results)
    # There should only be one plot
    result_axes = result_fig.axes
    assert len(result_axes) == 1
    # There should be four bars, grouped by trial, a different hue for each value
    assert len(result_axes[0].patches) == 4 + 2
    # TODO: More assertions required


def test_plot_series_values():
    """Test handling series results"""
    results = pd.DataFrame()
    results["value"] = [np.random.normal(0, 1, 100) for _ in range(3)]
    results["trial"] = ["t1", "t2", "t3"]
    results["name"] = "some_result"
    results["process"] = "some_proc"
    results["experiment"] = "some_experiment"

    result_fig = plot_results(results)
    # There should only be one plot
    result_axes = result_fig.axes
    assert len(result_axes) == 1
    # The plot should be a violin plot, with 3 violins
    # TODO: More assertions required


def test_plot_dataframe_values():
    """Test handling dataframe results"""
    results = pd.DataFrame()
    results["value"] = [pd.DataFrame(np.random.normal(0, 1, 100)) for _ in range(3)]
    results["trial"] = ["t1", "t2", "t3"]
    results["name"] = "some_result"
    results["process"] = "some_proc"
    results["experiment"] = "some_experiment"

    result_fig = plot_results(results)
    # There should only be one plot
    result_axes = result_fig.axes
    assert len(result_axes) == 1
    # The plot should be a line plot, with 3 lines
    # TODO: More assertions required


def test_plot_columns_rows():
    """Test handling multiple experiments and types of data"""
    results = pd.DataFrame()
    results["value"] = [
        1.0,
        pd.DataFrame(np.random.normal(0, 1, 100)),
        2.0,
        pd.DataFrame(np.random.normal(0, 1, 100)),
    ]
    results["trial"] = ["t1", "t1", "t2", "t2"]
    results["name"] = ["res1", "res2", "res1", "res2"]
    results["process"] = "some_proc"
    results["experiment"] = ["exp1", "exp1", "exp2", "exp2"]

    result_fig = plot_results(results)
    # There should be 4 plots in a 2x2 grid
    result_axes = result_fig.axes
    assert len(result_axes) == 4
